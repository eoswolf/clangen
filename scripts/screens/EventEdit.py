import pygame
import pygame_gui
import os
import platform
import subprocess

from scripts.events_module.generate_events import GenerateEvents
from scripts.game_structure.screen_settings import MANAGER
from scripts.game_structure.ui_elements import UISurfaceImageButton, UIModifiedScrollingContainer, UITextBoxTweaked
from scripts.screens.Screens import Screens
from scripts.ui.generate_box import get_box, BoxStyles
from scripts.ui.generate_button import get_button_dict, ButtonStyles
from scripts.ui.icon import Icon
from scripts.utility import ui_scale


class EventEdit(Screens):
    """
    This screen provides an interface to allow devs to edit and create events.
    """

    def __init__(self, name=None):
        super().__init__(name)

        self.editor_container = None
        self.add_button = None
        self.event_list_container = None
        self.event_list = None
        self.editor_frame = None
        self.list_frame = None
        self.main_menu_button = None

        self.type_tab_buttons = {}
        self.biome_tab_buttons = {}
        self.event_buttons = {}
        self.editor_element = {}

        self.chosen_type = None
        self.chosen_biome = None
        self.chosen_event = None

    def handle_event(self, event):
        if event.type == pygame_gui.UI_TEXT_BOX_LINK_CLICKED:
            if platform.system() == "Darwin":
                subprocess.Popen(["open", "-u", event.link_target])
            elif platform.system() == "Windows":
                os.system(f'start "" {event.link_target}')
            elif platform.system() == "Linux":
                subprocess.Popen(["xdg-open", event.link_target])

        if event.type == pygame_gui.UI_BUTTON_START_PRESS:
            self.mute_button_pressed(event)

            if event.ui_element == self.main_menu_button:
                self.change_screen("start screen")
                return

            elif event.ui_element in self.type_tab_buttons.values():
                for tab in self.type_tab_buttons:
                    if event.ui_element == self.type_tab_buttons[tab]:
                        self.chosen_type = tab

                self.select_biome_tab_creation()

            elif event.ui_element in self.biome_tab_buttons.values():
                if event.ui_element == self.biome_tab_buttons["back"]:
                    self.select_type_tab_creation()
                    self.event_list = None

                else:
                    for tab in self.biome_tab_buttons:
                        if event.ui_element == self.biome_tab_buttons[tab]:
                            self.chosen_biome = tab.capitalize() if tab != "general" else tab

                    self.display_events()

            elif event.ui_element in self.event_buttons.values():
                self.chosen_event = event.ui_element.text

            elif event.ui_element == self.add_button:
                self.chosen_event = None
                self.display_editor()

        pass

    def exit_screen(self):
        self.chosen_biome = None
        self.chosen_type = None

        self.main_menu_button.kill()
        self.list_frame.kill()
        self.editor_frame.kill()
        if self.event_list_container:
            self.event_list_container.kill()
        if self.editor_container:
            self.editor_container.kill()

        self.add_button.kill()
        self.kill_tabs()
        self.kill_event_buttons()

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
            ui_scale(pygame.Rect((60, 80), (250, 560))),
            get_box(BoxStyles.ROUNDED_BOX, (250, 560)),
            starting_height=2,
            manager=MANAGER,
        )

        self.select_type_tab_creation()

        self.editor_frame = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((300, 90), (470, 540))),
            get_box(BoxStyles.FRAME, (470, 540)),
            starting_height=1,
            manager=MANAGER,
        )
        self.add_button = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 580), (36, 36))),
            Icon.NOTEPAD,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.add_event"
        )

        self.editor_container = UIModifiedScrollingContainer(
            ui_scale(pygame.Rect((314, 104), (470, 540))),
            starting_height=3,
            manager=MANAGER,
            allow_scroll_y=True,
        )

        self.editor_element["intro_text"] = UITextBoxTweaked(
            "screens.event_edit.intro_text",
            ui_scale(pygame.Rect((0, 0), (450, -1))),
            object_id="#text_box_26_horizleft_pad_10_14",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container
        )

    def kill_tabs(self):
        for tab in self.type_tab_buttons:
            self.type_tab_buttons[tab].kill()
        for tab in self.biome_tab_buttons:
            self.biome_tab_buttons[tab].kill()

    def select_type_tab_creation(self):
        # clear all tabs first
        self.kill_tabs()

        self.type_tab_buttons["death"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 136), (36, 36))),
            Icon.STARCLAN,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.edit_deaths"
        )
        self.type_tab_buttons["injury"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 10), (36, 36))),
            Icon.SCRATCHES,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.edit_injuries",
            anchors={
                "top_target": self.type_tab_buttons["death"]
            }
        )
        self.type_tab_buttons["misc"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 10), (36, 36))),
            Icon.CLAN_UNKNOWN,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.edit_misc",
            anchors={
                "top_target": self.type_tab_buttons["injury"]
            }
        )
        self.type_tab_buttons["new_cat"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 10), (36, 36))),
            Icon.CAT_HEAD,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.edit_new_cat",
            anchors={
                "top_target": self.type_tab_buttons["misc"]
            }
        )

    def select_biome_tab_creation(self):
        # clear all tabs first
        self.kill_tabs()

        self.biome_tab_buttons["back"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 90), (36, 36))),
            Icon.ARROW_LEFT,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1
        )
        self.biome_tab_buttons["general"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 10), (36, 36))),
            Icon.PAW,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.edit_general",
            anchors={
                "top_target": self.biome_tab_buttons["back"]
            }
        )
        self.biome_tab_buttons["forest"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 10), (36, 36))),
            Icon.LEAFFALL,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.edit_forest",
            anchors={
                "top_target": self.biome_tab_buttons["general"]
            }
        )
        self.biome_tab_buttons["mountainous"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 10), (36, 36))),
            Icon.LEAFBARE,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.edit_mountain",
            anchors={
                "top_target": self.biome_tab_buttons["forest"]
            }
        )
        self.biome_tab_buttons["plains"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 10), (36, 36))),
            Icon.NEWLEAF,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.edit_plains",
            anchors={
                "top_target": self.biome_tab_buttons["mountainous"]
            }
        )
        self.biome_tab_buttons["beach"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 10), (36, 36))),
            Icon.DARKFOREST,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.edit_beach",
            anchors={
                "top_target": self.biome_tab_buttons["plains"]
            }
        )

        self.biome_tab_buttons["desert"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 10), (36, 36))),
            Icon.GREENLEAF,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.edit_desert",
            anchors={
                "top_target": self.biome_tab_buttons["beach"]
            }
        )

        self.biome_tab_buttons["wetlands"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((27, 10), (36, 36))),
            Icon.HERB,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.edit_wetlands",
            anchors={
                "top_target": self.biome_tab_buttons["desert"]
            }
        )

    def display_events(self):
        self.kill_event_buttons()
        self.event_list = None
        self.event_list = GenerateEvents.possible_short_events(self.chosen_type, self.chosen_biome)

        self.event_list_container = UIModifiedScrollingContainer(
            ui_scale(pygame.Rect((70, 90), (230, 540))),
            starting_height=3,
            manager=MANAGER,
            allow_scroll_y=True,
        )

        x = 0
        for event in self.event_list:
            self.event_buttons[x] = UISurfaceImageButton(
                ui_scale(pygame.Rect((0, 0), (230, 36))),
                event.event_id,
                get_button_dict(ButtonStyles.DROPDOWN, (230, 36)),
                manager=MANAGER,
                object_id="@buttonstyles_dropdown",
                starting_height=1,
                anchors={
                    "top_target": self.event_buttons[x - 1]
                } if self.event_buttons.get(x - 1) else None,
                container=self.event_list_container,
                tool_tip_text=event.text
            )
            x += 1

    def kill_event_buttons(self):
        for event in self.event_buttons:
            self.event_buttons[event].kill()

    def display_editor(self):

        self.editor_element["intro_text"].kill()


        self.editor_element["event_id_text"] = UITextBoxTweaked(
            "event_id:",
            ui_scale(pygame.Rect((0, 0), (-1, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container
        )

        self.editor_element["event_id_entry"] = pygame_gui.elements.UITextEntryLine(
            ui_scale(pygame.Rect((0, 3), (300, 29))),
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "left_target": self.editor_element["event_id_text"]
            }
        )
