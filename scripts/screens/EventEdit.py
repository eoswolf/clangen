import pygame
import pygame_gui
import os
import platform
import subprocess
import ujson
from itertools import chain

from scripts.game_structure.game_essentials import game
from scripts.game_structure.screen_settings import MANAGER
from scripts.game_structure.ui_elements import UISurfaceImageButton, UIModifiedScrollingContainer, UITextBoxTweaked, \
    UIDropDownContainer
from scripts.screens.Screens import Screens
from scripts.ui.generate_box import get_box, BoxStyles
from scripts.ui.generate_button import get_button_dict, ButtonStyles
from scripts.ui.icon import Icon
from scripts.utility import ui_scale


class EventEdit(Screens):
    """
    This screen provides an interface to allow devs to edit and create events.
    """

    all_camps = {
        "Forest": ["Classic", "Gully", "Grotto", "Lakeside"],
        "Mountainous": ["Cliff", "Cavern", "Crystal River", "Ruins"],
        "Plains": ["Grasslands", "Tunnels", "Wastelands"],
        "Beach": ["Tidepools", "Tidal Cave", "Shipwreck", "Fjord"]
    }
    all_seasons = ["newleaf", "greenleaf", "leaf-fall", "leaf-bare"]

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
        self.event_id_element = {}
        self.location_element = {}
        self.location_info = []
        self.season_element = {}
        self.season_info = []

        self.chosen_type = None
        self.chosen_biome = None
        self.chosen_event = None

        self.new_event = {}

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

            # CHANGE LOCATION LIST
            if event.ui_element in self.location_element.values():
                biome_list = game.clan.BIOME_TYPES
                for biome in biome_list:
                    if event.ui_element == self.location_element[biome]:
                        self.update_location_info(biome=biome)
                for camp in [camp for biome in self.all_camps.values() for camp in biome]:
                    if event.ui_element == self.location_element.get(camp):
                        self.update_location_info(camp=camp)

            # CHANGE SEASON LIST
            if event.ui_element in self.season_element.values():
                for season in self.all_seasons:
                    if event.ui_element == self.season_element[season]:
                        self.update_season_info(season)

        if event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
            # CHANGE EVENT ID
            if event.ui_element == self.event_id_element["event_id_entry"]:
                self.new_event.update({"event_id": self.event_id_element["event_id_entry"].text})

        pass

    def update_location_info(self, biome=None, camp=None):

        if biome:
            biome = biome.casefold()
            present = False
            for location in self.location_info:
                if biome in location:
                    present = True
            if not present:
                self.location_info.append(biome)
                self.update_camp_list(biome.capitalize())

            else:
                for location in self.location_info:
                    if biome in location:
                        self.location_info.remove(location)
                        self.update_camp_list(None)
                        break

        if camp:
            present = True
            parent_biome = None
            camp_index = 0
            old_location_tag = None
            new_string = None

            for camp_biome in self.all_camps.keys():
                if camp in self.all_camps[camp_biome]:
                    parent_biome = camp_biome
                    camp_index = self.all_camps[camp_biome].index(camp) + 1
                    break

            for location in self.location_info:
                if parent_biome.casefold() in location:
                    if f"camp{camp_index}" in location:
                        break
                    else:
                        new_string = f"{location}_camp{camp_index}"
                        present = False
                        old_location_tag = location
                        break
            if not present:
                self.location_info.remove(old_location_tag)
                self.location_info.append(new_string.casefold())
            else:
                for location in self.location_info:
                    if parent_biome.casefold() in location:
                        old_location_tag = location
                        new_string = location.replace(f"_camp{camp_index}", "")
                        break
                self.location_info.remove(old_location_tag)
                self.location_info.append(new_string)

        self.location_element["location_display"].set_text(str(self.location_info) if self.location_info else "['any']")
        self.editor_container.on_contained_elements_changed(self.location_element["location_display"])

    def update_season_info(self, season):

        if season in self.season_info:
            self.season_info.remove(season)
        else:
            self.season_info.append(season)

        if self.season_info:
            self.season_element["season_entry"].set_text(f"{self.season_info}")
        else:
            self.season_element["season_entry"].set_text("['any']")


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
            ui_scale(pygame.Rect((314, 100), (470, 520))),
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

        path = f"resources/lang/en/events/{self.chosen_type}/{self.chosen_biome.casefold()}.json"

        try:
            with open(path, "r", encoding="utf-8") as read_file:
                events = read_file.read()
                self.event_list = ujson.loads(events)
        except:
            print(f"Something went wrong with event loading. Is {path} valid?")

        if not self.event_list:
            self.editor_element["intro_text"].set_text("screens.event_edit.empty_event_list")
            return

        try:
            if not isinstance(self.event_list[0], dict):
                print(f"{path} isn't in the correct event format. Perhaps it isn't an event .json?")
        except KeyError:
            return

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
                event["event_id"],
                get_button_dict(ButtonStyles.DROPDOWN, (230, 36)),
                manager=MANAGER,
                object_id="@buttonstyles_dropdown",
                starting_height=1,
                anchors={
                    "top_target": self.event_buttons[x - 1]
                } if self.event_buttons.get(x - 1) else None,
                container=self.event_list_container,
                tool_tip_text=event["event_text"]
            )
            x += 1

    def kill_event_buttons(self):
        for event in self.event_buttons:
            self.event_buttons[event].kill()

    def display_editor(self):

        self.editor_element["intro_text"].kill()

        # EVENT ID
        self.event_id_element["event_id_text"] = UITextBoxTweaked(
            "event_id:",
            ui_scale(pygame.Rect((0, 0), (-1, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container
        )

        self.event_id_element["event_id_entry"] = pygame_gui.elements.UITextEntryLine(
            ui_scale(pygame.Rect((0, 3), (300, 29))),
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "left_target": self.event_id_element["event_id_text"]
            },
            placeholder_text="screens.event_edit.empty_event_id"
        )

        # LOCATION
        self.location_element["location_text"] = UITextBoxTweaked(
            "screens.event_edit.location_info",
            ui_scale(pygame.Rect((0, 10), (450, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.event_id_element["event_id_text"]
            }
        )

        biome_list = game.clan.BIOME_TYPES

        for biome in biome_list:
            y_pos = 10 if biome == biome_list[0] else 0
            self.location_element[biome] = UISurfaceImageButton(
                ui_scale(pygame.Rect((0, y_pos), (150, 30))),
                biome,
                get_button_dict(ButtonStyles.DROPDOWN, (150, 30)),
                manager=MANAGER,
                object_id="@buttonstyles_dropdown",
                container=self.editor_container,
                anchors={
                    "left_target": self.event_id_element["event_id_text"],
                    "top_target": (self.location_element["location_text"]
                                   if biome == biome_list[0]
                                   else self.location_element[biome_list[biome_list.index(biome) - 1]])
                }
            )

        self.location_element["location_display"] = UITextBoxTweaked(
            "['any']",
            ui_scale(pygame.Rect((10, 10), (470, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": (self.location_element[biome_list[-1]]),
            },
            allow_split_dashes=False
        )

        # SEASON
        self.season_element["season_text"] = UITextBoxTweaked(
            "screens.event_edit.season_info",
            ui_scale(pygame.Rect((0, 10), (450, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.location_element["location_display"]
            }
        )

        for season in self.all_seasons:
            y_pos = 10 if season == self.all_seasons[0] else 0
            self.season_element[season] = UISurfaceImageButton(
                ui_scale(pygame.Rect((0, y_pos), (150, 30))),
                season,
                get_button_dict(ButtonStyles.DROPDOWN, (150, 30)),
                manager=MANAGER,
                object_id="@buttonstyles_dropdown",
                container=self.editor_container,
                anchors={
                    "left_target": self.event_id_element["event_id_text"],
                    "top_target": (self.season_element["season_text"]
                                   if season == self.all_seasons[0]
                                   else self.season_element[self.all_seasons[self.all_seasons.index(season) - 1]])
                }
            )

        self.season_element["season_entry"] = UITextBoxTweaked(
            "['any']",
            ui_scale(pygame.Rect((10, 10), (470, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": (self.season_element[self.all_seasons[-1]]),
            },
            allow_split_dashes=False
        )

    def update_camp_list(self, chosen_biome):

        for biome in self.all_camps:
            for camp in self.all_camps[biome]:
                if self.location_element.get(camp):
                    self.location_element[camp].kill()

        camp_list = self.all_camps.get(chosen_biome)

        if not camp_list:
            return

        for camp in camp_list:
            y_pos = 10 if camp == camp_list[0] else 0
            self.location_element[camp] = UISurfaceImageButton(
                ui_scale(pygame.Rect((20, y_pos), (150, 30))),
                camp,
                get_button_dict(ButtonStyles.DROPDOWN, (150, 30)),
                manager=MANAGER,
                object_id="@buttonstyles_dropdown",
                container=self.editor_container,
                anchors={
                    "left_target": self.location_element[chosen_biome],
                    "top_target": (self.location_element["location_text"]
                                   if camp == camp_list[0]
                                   else self.location_element[camp_list[camp_list.index(camp) - 1]])
                }
            )
