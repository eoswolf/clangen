import pygame
import pygame_gui

from scripts.game_structure.screen_settings import MANAGER
from scripts.game_structure.ui_elements import UISurfaceImageButton
from scripts.screens.Screens import Screens
from scripts.ui.generate_box import get_box, BoxStyles
from scripts.ui.generate_button import get_button_dict, ButtonStyles
from scripts.utility import ui_scale


class EventEdit(Screens):
    """
    This screen provides an interface to allow devs to edit and create events.
    """

    def __init__(self, name=None):
        super().__init__(name)

    def handle_event(self, event):
        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            self.mute_button_pressed(event)

            if event.ui_element == self.main_menu_button:
                self.change_screen("start screen")
                return
        pass

    def exit_screen(self):
        self.main_menu_button.kill()

    def screen_switches(self):

        super().screen_switches()
        Screens.show_mute_buttons()

        self.main_menu_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((25, 25), (152, 30))),
            "buttons.main_menu",
            get_button_dict(ButtonStyles.SQUOVAL, (152, 30)),
            manager=MANAGER,
            object_id="@buttonstyles_squoval",
            starting_height=1,
        )

        self.list_frame = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((50, 70), (250, 580))),
            get_box(BoxStyles.ROUNDED_BOX, (250, 580)),
            starting_height=2,
            manager=MANAGER,
        )

        self.editor_frame = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((290, 80), (470, 560))),
            get_box(BoxStyles.FRAME, (470, 560)),
            starting_height=1,
            manager=MANAGER,
        )


