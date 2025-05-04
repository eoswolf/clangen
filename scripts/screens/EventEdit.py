from random import choice

import pygame
import pygame_gui
import os
import platform
import subprocess
import ujson
from itertools import chain

from scripts.cat.cats import Cat
from scripts.game_structure.game_essentials import game
from scripts.game_structure.screen_settings import MANAGER
from scripts.game_structure.ui_elements import UISurfaceImageButton, UIModifiedScrollingContainer, UITextBoxTweaked, \
    UIDropDownContainer, UICheckbox, UIModifiedImage
from scripts.screens.Screens import Screens
from scripts.ui.generate_box import get_box, BoxStyles
from scripts.ui.generate_button import get_button_dict, ButtonStyles
from scripts.ui.icon import Icon
from scripts.utility import ui_scale, process_text


class EventEdit(Screens):
    """
    This screen provides an interface to allow devs to edit and create events.
    """
    preview_states = ("off", 1, 2)
    test_cat_names = {
        "m_c": "MainCat",
        "r_c": "RandomCat",
        "n_c:1": "NewCat",
        "mur_c": "MurderedCat",
        "lead_name": "TestStar",
        "dep_name": "DepCat",
        "med_name": "MedCat"
    }
    test_pronouns = [
        {
            "subject": "they",
            "object": "them",
            "poss": "their",
            "inposs": "theirs",
            "self": "themself",
            "conju": 1
        },
        {
            "subject": "she",
            "object": "her",
            "poss": "her",
            "inposs": "hers",
            "self": "herself",
            "conju": 2
        },
        {
            "subject": "he",
            "object": "him",
            "poss": "his",
            "inposs": "his",
            "self": "himself",
            "conju": 2
        }
    ]

    all_camps = {
        "Forest": ["Classic", "Gully", "Grotto", "Lakeside"],
        "Mountainous": ["Cliff", "Cavern", "Crystal River", "Ruins"],
        "Plains": ["Grasslands", "Tunnels", "Wastelands"],
        "Beach": ["Tidepools", "Tidal Cave", "Shipwreck", "Fjord"]
    }
    all_seasons = ("newleaf", "greenleaf", "leaf-fall", "leaf-bare")

    event_types = {
        "death": ["murder", "old_age", "mass_death", "war"],
        "injury": ["war"],
        "misc": ["murder_reveal", "accessory", "ceremony", "war"],
        "new_cat": ["war"]
    }

    basic_tag_list = [
        {
            "tag": "classic",
            "setting": False,
            "required_type": None,
            "conflict": None
        },
        {
            "tag": "cruel_season",
            "setting": False,
            "required_type": None,
            "conflict": None
        },
        {
            "tag": "no_body",
            "setting": False,
            "required_type": "death",
            "conflict": None
        },
        {
            "tag": "clan_wide",
            "setting": False,
            "required_type": None,
            "conflict": None
        },
        {
            "tag": "romance",
            "setting": False,
            "required_type": None,
            "conflict": None
        },
        {
            "tag": "adoption",
            "setting": False,
            "required_type": None,
            "conflict": None
        },
        {
            "tag": "all_lives",
            "setting": False,
            "required_type": "death",
            "conflict": ["some_lives", "lives_remain"]
        },
        {
            "tag": "some_lives",
            "setting": False,
            "required_type": "death",
            "conflict": ["all_lives"]
        },
        {
            "tag": "lives_remain",
            "setting": False,
            "required_type": "death",
            "conflict": ["all_lives"]
        },
        {
            "tag": "high_lives",
            "setting": False,
            "required_type": None,
            "conflict": ["mid_lives", "low_lives"]
        },
        {
            "tag": "mid_lives",
            "setting": False,
            "required_type": None,
            "conflict": ["high_lives", "low_lives"]
        },
        {
            "tag": "low_lives",
            "setting": False,
            "required_type": None,
            "conflict": ["mid_lives", "high_lives"]
        }
    ]

    def __init__(self, name=None):
        super().__init__(name)

        self.event_text_container = None
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
        self.event_text_element = {}
        self.event_id_element = {}
        self.location_element = {}
        self.location_info = []
        self.season_element = {}
        self.season_info = []
        self.type_element = {}
        self.type_info = 'death'
        self.sub_element = {}
        self.sub_info = []
        self.tag_element = {}
        self.basic_tag_checkbox = {}
        self.rank_tag_checkbox = {}
        self.tag_info = []
        self.weight_element = {}
        self.weight_info = 20

        self.chosen_type = None
        self.chosen_biome = None
        self.chosen_event = None

        self.current_preview_state = self.preview_states[0]

        self.new_event = {}

    def handle_event(self, event):
        if event.type == pygame_gui.UI_TEXT_BOX_LINK_CLICKED:
            if platform.system() == "Darwin":
                subprocess.Popen(["open", "-u", event.link_target])
            elif platform.system() == "Windows":
                os.system(f'start "" {event.link_target}')
            elif platform.system() == "Linux":
                subprocess.Popen(["xdg-open", event.link_target])

        elif event.type == pygame_gui.UI_BUTTON_START_PRESS:
            self.mute_button_pressed(event)

            if event.ui_element == self.main_menu_button:

                self.change_screen("start screen")
                return

            elif event.ui_element == self.event_text_element["preview_button"]:
                # finds what the new preview state should be
                index = self.preview_states.index(self.current_preview_state)
                new_index = index + 1 if index + 1 <= 2 else 0
                self.current_preview_state = self.preview_states[new_index]

                # switches states
                if new_index == 0:
                    self.event_text_element["event_text"].show()
                    self.event_text_element["preview_text"].hide()
                else:
                    self.event_text_element["event_text"].hide()
                    text = self.event_text_element["event_text"].html_text

                    test_dict = {}
                    for abbr in self.test_cat_names:
                        pronoun = choice(
                            [pro for pro in self.test_pronouns if pro["conju"] == self.current_preview_state]
                        )
                        test_dict[abbr] = (
                            self.test_cat_names[abbr], pronoun
                        )

                    text = process_text(text, test_dict)
                    self.event_text_element["preview_text"].set_text(text)
                    self.event_text_element["preview_text"].show()

            elif event.ui_element in self.type_tab_buttons.values():
                for tab in self.type_tab_buttons:
                    if event.ui_element == self.type_tab_buttons[tab]:
                        self.chosen_type = tab
                        break

                self.select_biome_tab_creation()

            elif event.ui_element in self.biome_tab_buttons.values():
                if event.ui_element == self.biome_tab_buttons["back"]:
                    self.select_type_tab_creation()
                    self.event_list = None

                else:
                    for tab in self.biome_tab_buttons:
                        if event.ui_element == self.biome_tab_buttons[tab]:
                            self.chosen_biome = tab.capitalize() if tab != "general" else tab
                            break

                    self.display_events()

            elif event.ui_element in self.event_buttons.values():
                self.chosen_event = event.ui_element.text

            elif event.ui_element == self.add_button:
                # TODO: need prevention for clicking after editor is already open
                self.chosen_event = None
                self.display_editor()

            # CHANGE LOCATION LIST
            elif event.ui_element in self.location_element.values():
                biome_list = game.clan.BIOME_TYPES
                for biome in biome_list:
                    if event.ui_element == self.location_element[biome]:
                        self.update_location_info(biome=biome)
                        break
                for camp in [camp for biome in self.all_camps.values() for camp in biome]:
                    if event.ui_element == self.location_element.get(camp):
                        self.update_location_info(camp=camp)
                        break

            # CHANGE SEASON LIST
            elif event.ui_element in self.season_element.values():
                for season in self.all_seasons:
                    if event.ui_element == self.season_element[season]:
                        self.update_season_info(season)
                        break

            # CHANGE TYPE
            elif event.ui_element in self.type_element.values():
                if event.ui_element == self.type_element["pick_type"]:
                    (self.type_element["type_dropdown"].open()
                     if not self.type_element["type_dropdown"].is_open
                     else self.type_element["type_dropdown"].close())
                if event.ui_element in self.type_element["dropdown_container"].elements:
                    self.type_element["type_dropdown"].disable_child(event.ui_element)
                    self.type_element["type_dropdown"].close()
                    for event_type in self.event_types.keys():
                        if self.type_element["type_dropdown"].selected_element == self.type_element[event_type]:
                            self.type_element["pick_type"].set_text(event_type)
                            self.type_info = event_type
                            self.sub_info = []
                            self.update_sub_buttons(self.event_types.get(self.type_info))
                            self.update_basic_checkboxes()
                            break

            # CHANGE SUBTYPE
            elif event.ui_element in self.sub_element.values():
                for sub in self.event_types[self.type_info]:
                    if event.ui_element == self.sub_element[sub]:
                        self.update_sub_info(sub)
                        break

            # CHANGE BASIC TAGS
            elif event.ui_element in self.basic_tag_checkbox.values():
                event.ui_element.uncheck() if event.ui_element.checked else event.ui_element.check()
                for info in self.basic_tag_list:
                    if event.ui_element == self.basic_tag_checkbox.get(info["tag"]):
                        index = self.basic_tag_list.index(info)
                        self.basic_tag_list[index] = {
                            "tag": info["tag"],
                            "setting": False if info["setting"] else True,
                            "required_type": info["required_type"],
                            "conflict": info["conflict"]
                        }

                        # flip the setting of any conflicting tags
                        if info["conflict"]:
                            for tag in info["conflict"]:
                                conflict_info = [block for block in self.basic_tag_list if tag == block["tag"]][0]
                                conflict_index = self.basic_tag_list.index(conflict_info)
                                if not info["setting"]:  # unchecks if conflicted setting is checked
                                    self.basic_tag_checkbox[tag].uncheck()
                                self.basic_tag_list[conflict_index] = {
                                    "tag": conflict_info["tag"],
                                    "setting": False,
                                    "required_type": conflict_info["required_type"],
                                    "conflict": conflict_info["conflict"]
                                }

                        self.update_tag_info()
                        break

            # CHANGE RANK TAGS
            elif event.ui_element in self.rank_tag_checkbox.values():
                event.ui_element.uncheck() if event.ui_element.checked else event.ui_element.check()
                self.update_tag_info()

        elif event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
            # CHANGE EVENT ID
            if event.ui_element == self.event_id_element["event_id_entry"]:
                self.new_event.update({"event_id": self.event_id_element["event_id_entry"].text})

        pass

    def update_tag_info(self):

        for info in self.basic_tag_list:
            if info["tag"] not in self.tag_info and info["setting"]:
                self.tag_info.append(info["tag"])
            elif info["tag"] in self.tag_info and not info["setting"]:
                self.tag_info.remove(info["tag"])

        for rank, box in self.rank_tag_checkbox.items():
            tag = f"clan:{rank}".replace(" ", "_")
            if box.checked and tag not in self.tag_info:
                self.tag_info.append(tag)
            elif not box.checked and tag in self.tag_info:
                self.tag_info.remove(tag)

        if self.tag_element.get("tag_display"):
            self.tag_element["tag_display"].set_text(f"chosen tags: {self.tag_info}")
            self.editor_container.on_contained_elements_changed(self.tag_element["tag_display"])

    def update_location_info(self, biome=None, camp=None):

        if biome:
            biome = biome.casefold()
            present = False
            for location in self.location_info:
                if biome in location:
                    present = True
                    break
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

        self.location_element["location_display"].set_text((f"chosen location: {str(self.location_info)}"
                                                            if self.location_info
                                                            else "chosen location: ['any']"))
        self.editor_container.on_contained_elements_changed(self.location_element["location_display"])

    def update_season_info(self, season):

        if season in self.season_info:
            self.season_info.remove(season)
        else:
            self.season_info.append(season)

        if self.season_info:
            self.season_element["season_display"].set_text(f"chosen season: {self.season_info}")
        else:
            self.season_element["season_display"].set_text("chosen season: ['any']")

    def update_sub_info(self, sub):

        if sub in self.sub_info:
            self.sub_info.remove(sub)
        else:
            self.sub_info.append(sub)

        if self.sub_info:
            self.sub_element["sub_display"].set_text(f"chosen subtypes: {self.sub_info}")
        else:
            self.sub_element["sub_display"].set_text("chosen subtypes: []")

    def exit_screen(self):
        self.chosen_biome = None
        self.chosen_type = None
        self.chosen_event = None
        self.location_info = []
        self.season_info = []
        self.type_info = []
        self.sub_info = []
        self.tag_info = []

        self.main_menu_button.kill()
        self.list_frame.kill()
        self.editor_frame.kill()
        self.event_text_container.kill()
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
            starting_height=3,
            manager=MANAGER,
        )

        self.select_type_tab_creation()

        self.event_text_container = pygame_gui.elements.UIAutoResizingContainer(
            ui_scale(pygame.Rect((290, 30), (0, 0))),
            starting_height=1,
            manager=MANAGER,
        )
        self.event_text_element["preview_button"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((-30, 10), (36, 36))),
            Icon.MAGNIFY,
            get_button_dict(ButtonStyles.ICON_TAB_RIGHT, (36, 36)),
            manager=MANAGER,
            container=self.event_text_container,
            object_id="@buttonstyles_icon_tab_right",
            starting_height=1,
            tool_tip_text="buttons.preview_text"
        )

        self.event_text_element["box"] = UIModifiedImage(
            ui_scale(pygame.Rect((0, 0), (460, 120))),
            get_box(BoxStyles.ROUNDED_BOX, (460, 120)),
            starting_height=1,
            manager=MANAGER,
            container=self.event_text_container
        )
        self.event_text_element["box"].disable()

        self.editor_frame = pygame_gui.elements.UIImage(
            ui_scale(pygame.Rect((300, 140), (470, 490))),
            get_box(BoxStyles.FRAME, (470, 490)),
            starting_height=2,
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
            ui_scale(pygame.Rect((314, 150), (470, 470))),
            starting_height=4,
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
        if self.editor_element.get("intro_text"):
            self.editor_element["intro_text"].set_text("screens.event_edit.intro_text")

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

        # EVENT TEXT
        # this one is special in that it has a separate container
        self.event_text_element["preview_text"] = UITextBoxTweaked(
            "",
            ui_scale(pygame.Rect((48, 10), (435, 100))),
            object_id="#text_box_26_horizleft_pad_10_14",
            manager=MANAGER,
            container=self.event_text_container,
            visible=False,
        )
        self.event_text_element["preview_text"].disable()
        self.event_text_element["event_text"] = pygame_gui.elements.UITextEntryBox(
            ui_scale(pygame.Rect((48, 10), (435, 100))),
            placeholder_text="screens.event_edit.event_text_initial",
            object_id="#text_box_26_horizleft_pad_10_14",
            manager=MANAGER,
            container=self.event_text_container,
        )

        # EVENT ID
        self.create_event_id_editor()

        # LOCATION
        self.create_location_editor()

        # SEASON
        self.create_season_editor()

        # TYPE
        self.create_type_editor()

        # SUBTYPE
        self.create_subtype_editor()

        # TAGS
        self.create_basic_tag_editor()
        self.create_rank_tag_editor()

        # WEIGHT
        self.create_weight_editor()

    def create_weight_editor(self):
        self.weight_element["weight_text"] = UITextBoxTweaked(
            "<b>weight:</b>",
            ui_scale(pygame.Rect((0, 10), (-1, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.tag_element["tag_display"]
            }
        )
        self.weight_element["weight_entry"] = pygame_gui.elements.UITextEntryLine(
            ui_scale(pygame.Rect((0, 13), (50, 29))),
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.tag_element["tag_display"],
                "left_target": self.weight_element["weight_text"]
            },
            initial_text=f"{self.weight_info}"
        )

    def create_rank_tag_editor(self):
        self.tag_element["rank_tag_text"] = UITextBoxTweaked(
            "screens.event_edit.rank_tags",
            ui_scale(pygame.Rect((0, 10), (250, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.tag_element["basic_checkbox_container"],
                "left_target": self.tag_element["tag_text"],

            }
        )
        prev_element = None
        rank_list = Cat.rank_sort_order
        rank_list.append("apps")
        for rank in rank_list:
            self.rank_tag_checkbox[rank] = UICheckbox(
                position=(400, 10),
                container=self.editor_container,
                manager=MANAGER,
                check=False,
                anchors={
                    "top_target": (prev_element if
                                   prev_element else
                                   self.tag_element["rank_tag_text"]),
                }
            )

            check_box_rect = pygame.Rect((0, 10), (350, -1))
            check_box_rect.right = -70
            if rank == "apps":
                rank_string = f"two of any apprentice type"
            else:
                rank_string = f"two {rank}s" if rank not in ("deputy", "leader") else rank
            self.tag_element[f"{rank}_text"] = UITextBoxTweaked(
                rank_string,
                ui_scale(check_box_rect),
                object_id="#text_box_30_horizright_pad_10_10",
                line_spacing=1,
                manager=MANAGER,
                container=self.editor_container,
                anchors={
                    "top_target": (prev_element if
                                   prev_element else
                                   self.tag_element["rank_tag_text"]),
                    "right": "right"
                }
            )

            prev_element = self.tag_element[f"{rank}_text"]
        self.tag_element["tag_display"] = UITextBoxTweaked(
            "chosen tags: []",
            ui_scale(pygame.Rect((10, 10), (470, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": prev_element,
            },
            allow_split_dashes=False
        )

    # TODO: maybe merge tag editors together?
    def create_basic_tag_editor(self):
        self.tag_element["tag_text"] = UITextBoxTweaked(
            "<b>tags:</b>",
            ui_scale(pygame.Rect((0, 10), (-1, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.sub_element["sub_display"]
            }
        )
        self.tag_element["basic_checkbox_container"] = pygame_gui.elements.UIAutoResizingContainer(
            ui_scale(pygame.Rect((0, 0), (0, 0))),
            container=self.editor_container,
            manager=MANAGER,
            anchors={
                "top_target": self.tag_element["tag_text"],
                "left_target": self.tag_element["tag_text"],
            }
        )
        self.update_basic_checkboxes()

    def update_basic_checkboxes(self):
        prev_element = None

        # clear old elements
        for info in self.basic_tag_list:
            if self.tag_element.get(f"{info['tag']}_text"):
                self.tag_element[f"{info['tag']}_text"].kill()
            if self.basic_tag_checkbox.get(info["tag"]):
                self.basic_tag_checkbox[info["tag"]].kill()

        # make new ones!
        for info in self.basic_tag_list:
            # first reset the values
            if info.get("required_type") and info["required_type"] != self.type_info:
                index = self.basic_tag_list.index(info)
                self.basic_tag_list[index] = {
                    "tag": info["tag"],
                    "setting": False,
                    "required_type": info["required_type"],
                    "conflict": info["conflict"]
                }
                continue

            self.tag_element[f"{info['tag']}_text"] = UITextBoxTweaked(
                f"screens.event_edit.{info['tag']}",
                ui_scale(pygame.Rect((0, 10), (350, -1))),
                object_id="#text_box_30_horizleft_pad_10_10",
                line_spacing=1,
                manager=MANAGER,
                container=self.tag_element["basic_checkbox_container"],
                anchors={
                    "top_target": prev_element,
                } if prev_element else None
            )

            self.basic_tag_checkbox[info["tag"]] = UICheckbox(
                position=(350, 10),
                container=self.tag_element["basic_checkbox_container"],
                manager=MANAGER,
                check=info["setting"],
                anchors={
                    "top_target": (self.tag_element["tag_text"]
                                   if not prev_element
                                   else prev_element)
                }
            )

            prev_element = self.tag_element[f"{info['tag']}_text"]

        self.update_tag_info()

    def create_subtype_editor(self):
        self.sub_element["sub_text"] = UITextBoxTweaked(
            "screens.event_edit.subtype_info",
            ui_scale(pygame.Rect((0, 10), (450, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.type_element["pick_type"]
            }
        )
        self.sub_element["container"] = pygame_gui.elements.UIAutoResizingContainer(
            ui_scale(pygame.Rect((0, 0), (0, 0))),
            container=self.editor_container,
            manager=MANAGER,
            anchors={
                "top_target": self.sub_element["sub_text"],
                "left_target": self.event_id_element["event_id_text"],
            }
        )

        self.update_sub_buttons(self.event_types[self.type_info])

        self.sub_element["sub_display"] = UITextBoxTweaked(
            "chosen subtypes: []",
            ui_scale(pygame.Rect((10, 10), (470, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.sub_element["container"],
            },
            allow_split_dashes=False
        )

    def update_sub_buttons(self, type_list):
        # remove old buttons
        for parent in self.event_types:
            for sub in self.event_types[parent]:
                if self.sub_element.get(sub):
                    self.sub_element[sub].kill()

        # make new buttons
        prev_element = None
        for sub in type_list:
            y_pos = 10 if not prev_element else 0
            self.sub_element[sub] = UISurfaceImageButton(
                ui_scale(pygame.Rect((50, y_pos), (150, 30))),
                sub,
                get_button_dict(ButtonStyles.DROPDOWN, (150, 30)),
                manager=MANAGER,
                object_id="@buttonstyles_dropdown",
                container=self.sub_element["container"],
                anchors={
                    "left_target": self.event_id_element["event_id_text"],
                    "top_target": (self.sub_element["sub_text"]
                                   if not prev_element
                                   else prev_element)
                }
            )
            prev_element = self.sub_element[sub]

        self.editor_container.on_contained_elements_changed(self.sub_element["container"])

        return prev_element

    def create_type_editor(self):
        self.type_element["type_text"] = UITextBoxTweaked(
            "<b>* type:</b>",
            ui_scale(pygame.Rect((0, 10), (-1, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            line_spacing=1,
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": self.season_element["season_display"]
            }
        )
        self.type_element["pick_type"] = UISurfaceImageButton(
            ui_scale(pygame.Rect((0, 13), (150, 30))),
            "buttons.pick_type",
            get_button_dict(ButtonStyles.DROPDOWN, (150, 30)),
            manager=MANAGER,
            object_id="@buttonstyles_dropdown",
            container=self.editor_container,
            anchors={
                "left_target": self.event_id_element["event_id_text"],
                "top_target": (self.season_element["season_display"])
            }
        )
        self.type_element["dropdown_container"] = pygame_gui.elements.UIAutoResizingContainer(
            ui_scale(pygame.Rect((0, 0), (0, 0))),
            manager=MANAGER,
            container=self.editor_container,
            starting_height=4,
            anchors={
                "left_target": self.event_id_element["event_id_text"],
                "top_target": self.type_element["pick_type"]
            }
        )
        big_types = list(self.event_types.keys())
        for event_type in big_types:
            self.type_element[event_type] = UISurfaceImageButton(
                ui_scale(pygame.Rect((0, 0), (150, 30))),
                event_type,
                get_button_dict(ButtonStyles.DROPDOWN, (150, 30)),
                manager=MANAGER,
                object_id="@buttonstyles_dropdown",
                container=self.type_element["dropdown_container"],
                anchors={
                    "top_target": (self.type_element["pick_type"]
                                   if event_type == big_types[0]
                                   else self.type_element[big_types[big_types.index(event_type) - 1]])
                }
            )
        self.type_element["dropdown_container"].hide()
        self.type_element["type_dropdown"] = UIDropDownContainer(
            ui_scale(pygame.Rect((0, 0), (0, 0))),
            container=self.editor_container,
            parent_button=self.type_element["pick_type"],
            child_button_container=self.type_element["dropdown_container"],
            manager=MANAGER
        )

    def create_season_editor(self):
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
        self.season_element["season_display"] = UITextBoxTweaked(
            "chosen season: ['any']",
            ui_scale(pygame.Rect((10, 10), (470, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": (self.season_element[self.all_seasons[-1]]),
            },
            allow_split_dashes=False
        )

    def create_location_editor(self):
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
            "chosen location: ['any']",
            ui_scale(pygame.Rect((10, 10), (470, -1))),
            object_id="#text_box_30_horizleft_pad_10_10",
            manager=MANAGER,
            container=self.editor_container,
            anchors={
                "top_target": (self.location_element[biome_list[-1]]),
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

    def create_event_id_editor(self):
        self.event_id_element["event_id_text"] = UITextBoxTweaked(
            "<b>* event_id:</b>",
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
