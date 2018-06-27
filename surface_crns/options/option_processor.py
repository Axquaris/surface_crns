import SCC.readers as scc_readers
from SCC.constants import *
from SCC.options.option_types import *
from SCC.models.simulation_grid import SimulationGrid
from SCC import random_color as rcolor
import numpy as np
import random


class SurfaceCRNOptionParser:
    def __init__(self, options):
        self.movie_title = self.process_movie_title(options)
        self.speedup_factor = self.process_speedup_factor(options)
        self.debug = self.process_debug_flag(options)
        self.rng_seed = self.process_rng_seed(options)
        self.max_duration = self.process_max_duration(options)
        self.capture_rate = self.process_capture_rate(options)
        self.fps = self.process_fps(options)
        self.display_text = self.process_display_text_flag(options)
        self.COLORMAP = self.process_colormap(options)
        self.simulation_type = self.process_simulation_type(options)
        if self.simulation_type == 'synchronous':
            self.update_rule = self.process_update_rule(options)
        elif self.simulation_type == 'asynchronous':
            self.transition_rules = self.process_transition_rules(options)
        self.init_state = self.process_init_state(options)
        self.pixels_per_node = self.process_pixels_per_node(options)
        self.grid_type = self.process_grid_type(options)
        if self.grid_type == 'parallel_emulated' or \
           self.grid_type == 'overlayed_emulated':
           self.emulation_colormap = self.process_emulation_colormap(options)
           self.horizontal_buffer = self.process_horizontal_buffer(options)
           self.vertical_buffer = self.process_vertical_buffer(options)
           self.cell_height = self.process_cell_height(options)
           self.cell_width = self.process_cell_width(options)
           self.representative_cell_x = self.process_representative_cell_x(options)
           self.representative_cell_y = self.process_representative_cell_y(options)
        self.capture_directory = self.process_capture_directory(options)

    def process_movie_title(self, options):
        if 'movie_title' in options:
            movie_title = options['movie_title']
        else:
            movie_title = None
        self.saving_movie = (movie_title != None)
        return movie_title

    def process_speedup_factor(self, options):
        if 'speedup_factor' in options:
            speedup_factor = float(options['speedup_factor'])
        else:
            speedup_factor = 1
        return speedup_factor

    def process_debug_flag(self, options):
        if 'debug' in options:
            debug_flag = options['debug'].lower()
            if debug_flag in ['true', 'on', 'yes']:
                DEBUG = True
            elif debug_flag in ['false', 'off', 'no']:
                DEBUG = False
            else:
                DEBUG = bool(int(options['debug']))
        else:
            DEBUG = False
        return DEBUG

    def process_rng_seed(self, options):
        RNG_SEED = RNGSeedOpt.from_manifest(options)
        return RNG_SEED

    def process_max_duration(self, options):
        if 'max_duration' in options:
            SIMULATION_DURATION = float(options['max_duration'])
        else:
            SIMULATION_DURATION = 1000000
        return SIMULATION_DURATION

    def process_capture_rate(self, options):
        if 'frame_capture_rate' in options:
            capture_rate = int(options['frame_capture_rate'])
        else:
            capture_rate = 5
        return capture_rate

    def process_fps(self, options):
        if 'fps' in options:
            fps = int(options['fps'])
        else:
            fps = 60
        return fps

    def process_display_text_flag(self, options):
        if 'node_display' in options:
            node_display = options['node_display'].lower()
            if node_display in ['yes', 'true', 'text']:
                display_text = True
            elif node_display in ['no', 'false', 'color']:
                display_text = False
            else:
                raise Exception('Unknown flag "' + options['node_display'] +
                                '" for option "node_display".')
        else:
            display_text = False
        return display_text

    def process_colormap(self, options):
        if 'colormap' in options:
            COLORMAP = options['colormap']
            if self.debug:
                print("Colormap:\n" + str(COLORMAP))
        else:
            print("No colormap defined. Setting colors randomly.")
            COLORMAP = dict()
        return COLORMAP

    def process_simulation_type(self, options):
        if 'totalistic_rule' in options:
            return 'synchronous'
        elif 'transition_rules' in options:
            return 'asynchronous'
        else:
            raise Exception("Transition rules or totalistic update rule " +
                            "required.")

    def process_update_rule(self, options):
        return options['totalistic_rule']

    def process_transition_rules(self, options):
        transition_rules = options['transition_rules']
            # Check validity of rules and add colors if necessary.
        random.seed(12312)   # RNG seed for color generation.
        for rule in transition_rules:
            # Check that reactions are unimolecular or bimolecular
            if len(rule.inputs) != len(rule.outputs):
                raise Exception("Invalid transition rule " + str(rule) +
                                "\nTransition rules for a surface CRN " +
                                "must have the same number of inputs and " +
                                "outputs.")
            if len(rule.inputs) > 2:
                raise Exception("Invalid transition rule " + str(rule) +
                                "\nOnly transition rules between one or " +
                                "two species are allowed in this " +
                                "implementation.")
            # Figure out colors for any states not set
            for node in rule.inputs + rule.outputs:
                self.update_colormap(node)
        if self.debug:
            print("Transition rules:\n" + str(transition_rules))
            print("Colormap:\n" + str(self.COLORMAP))
        return transition_rules

    def process_init_state(self, options):
        if 'init_state' in options:
            init_state = options['init_state']
            # Check for any new states that don't have color definitions
            random.seed(12312)   # RNG seed for color generation.
            # If numpy version too low, have to iterate without nditer
            np_version = np.__version__.split('.')
            if int(np_version[1]) >= 7:
                for node_state in np.nditer(init_state):
                    self.update_colormap(str(node_state))
            else:
                for line in init_state:
                    for node_state in line:
                        self.update_colormap(str(node_state))
            self.grid = SimulationGrid(init_state.shape[0], init_state.shape[1])
            self.grid.set_global_state(init_state)
            return init_state
        else:
            raise Exception("Initial grid state required.")

    def process_pixels_per_node(self, options):
        if 'pixels_per_node' in options:
            pixels_per_node = int(options['pixels_per_node'])
        else:
            pixels_per_node = 5
        return pixels_per_node

    def process_grid_type(self, options):
        if not 'grid_type' in options:
            grid_type = 'standard'
        else:
            grid_type = options['grid_type']
        return grid_type

    def process_emulation_colormap(self, options):
        if 'emulation_colormap' in options:
            if options['emulation_colormap'] == 'game_of_life':
                return {COLOR_CLASSES:{"On" :["1"],"Off":["0"],
                                       "Undefined":["B"]},
                        "0":(0, 0, 0),
                        "1":(200, 200, 200),
                        "B":(175, 0,   0)}
            else:
                raise Exception("Sorry, only the Game of Life emulation " +
                                "colormap is supported at this time.")

    def process_horizontal_buffer(self, options):
        if not 'horizontal_buffer' in options:
            raise Exception("Attribute horizontal buffer required for emulated"\
                            + " grids")
        return int(options['horizontal_buffer'])

    def process_vertical_buffer(self, options):
        if not 'vertical_buffer' in options:
            raise Exception("Attribute vertical buffer required for emulated"\
                            + " grids")
        return int(options['vertical_buffer'])

    def process_cell_height(self, options):
        if not 'cell_height' in options:
            raise Exception("Attribute cell_height required for emulated " +\
                            "grids")
        return int(options['cell_height'])

    def process_cell_width(self, options):
        if not 'cell_width' in options:
            raise Exception("Attribute cell_width required for emulated " +\
                            "grids")
        return int(options['cell_width'])

    def process_representative_cell_x(self, options):
        if not 'representative_cell_x' in options:
            raise Exception("Attribute representative_cell_x required for " +\
                            "emulated grids")
        return int(options['representative_cell_x'])

    def process_representative_cell_y(self, options):
        if not 'representative_cell_y' in options:
            raise Exception("Attribute representative_cell_y required for " +\
                            "emulated grids")
        return int(options['representative_cell_y'])

    def process_capture_directory(self, options):
        if 'capture_directory' in options:
            capture_directory = options['capture_directory']
        else:
            capture_directory = './'
        return capture_directory

    def update_colormap(self, state):
        if not state in self.COLORMAP.keys():
            colormap_values = [self.COLORMAP[key] for key in self.COLORMAP \
                                     if key != COLOR_CLASSES]
            self.COLORMAP[state] = \
                        rcolor.generate_new_color(colormap_values,0)

