### Importing Modules
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from multiprocessing import Pool
import warnings
from matplotlib.widgets import RectangleSelector 
import sys

### Mandlebrot calculation settings
MAX_ITER = 250 #Maximum number of Mandlebrot calculation iterations
LIM = 2 #Limit of Mandlebrot result value

### Defining functions
def make_plane(WIDTH, HEIGHT, X_OFFSET, Y_OFFSET, XPIX, YPIX): 
    '''Creates complex plane for Mandlebrot calculations.'''
    return np.array([[complex(x,y) for x in np.linspace(X_OFFSET-WIDTH/2,X_OFFSET+WIDTH/2,XPIX)] for y in np.linspace(Y_OFFSET-HEIGHT/2,Y_OFFSET+HEIGHT/2,YPIX)])

def mandle(i):
    '''Takes complex plane input and outputs pixel value.'''
    warnings.filterwarnings('ignore', category=RuntimeWarning) # Prevents runtime warnings from begin shown during calculations
    count = 1
    out = z = np.zeros(i.shape)
    while count < MAX_ITER:
            out += (z > LIM)*count*(out == 0)
            z = z*z+i
            count += 1
    out = (out == 0)*MAX_ITER + (out != 0)*out
    colored = np.transpose([[i, 1.5*(i-85)*(i>85), 3*(i-170)*(i>170)] for i in out], (0, 2, 1)).astype('uint8')
    return colored

### Creating Plot
f, ax = plt.subplots()
f.frameon = False
ax.set(navigate=False)
ax.set_axis_off()

### Mandlebrot Viewer class – Deals with user input and displaying mandlebrot set
class Viewer :
    XPIX = 512*2
    YPIX =384*2

    def __init__(self, ax): # Initiation function
        print('Initiating...\n')
        '''Default settings are x and y from -1 to 1 centered at the origin'''
        self.width = 2 
        self.height = 2*self.YPIX/self.XPIX
        self.center = [0,0]
        '''Creating default mandlebrot image'''
        self.ax=ax
        self.cp = make_plane(self.width, self.height, self.center[0], self.center[1], self.XPIX, self.YPIX)
        '''Using Pool() to perform the mandlebrot calculation on all four cores simultaneously'''
        self.mandle = Pool().map(mandle, np.array_split(self.cp, 4, axis=1))
        self.mandle = np.hstack((self.mandle[i] for i in range(4)))
        self.pic = plt.imshow(self.mandle, interpolation='none')
        '''Connecting user input events to the corresponding function'''
        self.cid_click = ax.get_figure().canvas.mpl_connect('button_press_event', self.click)
        self.rect_select = RectangleSelector(self.ax, lambda x, y: self.rect(x, y, self), drawtype='box', minspanx=5, minspany=5)
        self.cid_key = ax.get_figure().canvas.mpl_connect('key_press_event', self.key)
        '''Displaying intro message'''
        print('~~~~~ Welcome to MandleBro! ~~~~~ \n\n%%% Mouse Controls %%% \n-Double click to zoom in on a point. \n-Left click and drag to zoom in on a rectangle. \n-Right click to zoom out. \n%%% Keyboard Controls %%% \n-Press [R] to return to the default view. \n-Press [H] to save a high quality version of the displayed section (slow on Pi). \n-Press [Q] to quit. \n~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n')


    def rect(event, start, end, self): # Function called for rectangle zoom
        print('Zooming in on selection...')
        '''Converting rectangular selection input into complex plane values'''
        i = [self.center[0]+start.xdata*self.width/self.XPIX-self.width/2, self.center[1]+start.ydata*self.height/self.YPIX-self.height/2]
        f = [self.center[0]+end.xdata*self.width/self.XPIX-self.width/2, self.center[1]+end.ydata*self.height/self.YPIX-self.height/2]
        self.rect_select.set_active(False)
        '''Reassigning center, width and height values for Mandlebrot calculation'''
        self.center = [(i[0]+f[0])/2, (i[1]+f[1])/2]
        self.width = abs(f[0]-i[0])
        self.height = self.width*self.YPIX/self.XPIX
        '''Performing Mandlebrot calculation for new portion of complex plane and displaying'''
        self.cp = make_plane(self.width, self.height, self.center[0], self.center[1], self.XPIX, self.YPIX)
        self.mandle = np.hstack(Pool().map(mandle, np.array_split(self.cp, 4, axis=1)))
        self.pic.set_data(self.mandle)
        self.ax.get_figure().canvas.draw()
        print('Done!\n')
        '''Resetting rectangle selection tool by definining it. Otherwise it causes problems'''
        self.rect_select = RectangleSelector(self.ax, lambda x, y: self.rect(x, y, self), drawtype='box', minspanx=5, minspany=5)
        self.rect_select.set_active(True)

    def key(self, event):
        if event.button in ['R', 'r'] :
            print('[R] Reset\n')
            self.center = [0,0]
            self.width = 2
            self.height = 2*self.YPIX/self.XPIX
            print('Calculating values...')
            self.cp = make_plane(self.width, self.height, self.center[0], self.center[1], self.XPIX, self.YPIX)
            self.mandle = np.hstack(Pool().map(mandle, np.array_split(self.cp, 4, axis=1)))
            self.pic.set_data(self.mandle)
            self.ax.get_figure().canvas.draw()
            print('Done!\n')

        if event.button in ['H', 'h'] :
            print('[H] High quality render')
            self.cp = make_plane(self.width, self.height, self.center[0], self.center[1], self.XPIX*2, self.YPIX*2)
            print('Rendering figure. This may take a while, sit tight...')
            self.mandle = np.hstack(Pool().map(mandle, np.array_split(self.cp, 4, axis=1)))
            self.pic.set_data(self.mandle)
            title = input('What would you like to name your file?\n')
            self.ax.get_figure().savefig(title+'.eps', format='eps')
            print('Saved!\n')

        if event.button in ['Q' , 'q'] :
            print('[Q] Quit')
            sys.exit(0)


    def click(self, event): # Function called for click zoom
        '''Zooms in on clicked point when left clicked. Zooms out on right click.'''
        if event.button == 1 and event.dblclick == True: #Zooming in
            print('Zooming in on selected point...')
            self.center = [(event.xdata/self.XPIX-0.5)*self.width+self.center[0], (event.ydata/self.YPIX-0.5)*self.height+self.center[1]]
            self.width = self.width*0.7
            self.height = self.height*0.7
            self.cp = make_plane(self.width, self.height, self.center[0], self.center[1], self.XPIX, self.YPIX)
            self.mandle = np.hstack(Pool().map(mandle, np.array_split(self.cp, 4, axis=1)))
            self.pic.set_data(self.mandle)
            self.ax.get_figure().canvas.draw()
            print('Done!\n')

        if event.button == 3 : #Zooming out
            print('Zooming out...')
            self.width = self.width / 0.7
            self.height = self.height / 0.7
            self.cp = make_plane(self.width, self.height, self.center[0], self.center[1], self.XPIX, self.YPIX)
            self.mandle = np.hstack(Pool().map(mandle, np.array_split(self.cp, 4, axis=1)))
            self.pic.set_data(self.mandle)
            self.ax.get_figure().canvas.draw()
            print('Done!')

view = Viewer(ax)
plt.show()
