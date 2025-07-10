from typing import List

from scripts.cat.personality import Personality
from scripts.cat.skills import SkillPath
from scripts.game_structure import constants


class ShortEvent:
    """
    A moon event that only affects the moon it was triggered on.  Can involve two cats directly and be restricted by various constraints.
    - full documentation available on GitHub wiki
    """

    num_of_traits = len(Personality.trait_ranges["normal_traits"].keys()) + len(
        Personality.trait_ranges["kit_traits"].keys()
    )
    num_of_skills = len([*SkillPath])

    num_of_ages = 7  # can't pull this from the Cat file bc of circular imports

    def __init__(
        self,
        event_id: str = "",
        location: List[str] = None,
        season: List[str] = None,
        sub_type: List[str] = None,
        tags: List[str] = None,
        weight: int = 1,
        rarity: int = 4,
        text: str = "",
        new_accessory: List[str] = None,
        m_c=None,
        r_c=None,
        new_cat: List[list] = None,
        injury: list = None,
        exclude_involved: list = None,
        history: list = None,
        relationships: list = None,
        outsider: dict = None,
        other_clan: dict = None,
        supplies: list = None,
        new_gender: List[str] = None,
        future_event: dict = None,
    ):
        if not event_id:
            print("WARNING: moon event has no event_id")

        self.weight = weight

        self.event_id = event_id
        self.location = location if location else ["any"]
        if "any" not in self.location:
            self.weight += 1
        self.season = season if season else ["any"]
        if "any" not in self.season:
            self.weight += len(constants.SEASONS) - len(
                self.season
            )  # this increases the weight inversely to the number of season constraints
        self.sub_type = sub_type if sub_type else []
        self.tags = tags if tags else []
        self.rarity = rarity
        self.text = text
        self.new_accessory = new_accessory if new_accessory else []
        self.m_c = m_c if m_c else {"age": ["any"]}
        if self.m_c:
            if "age" not in self.m_c:
                self.m_c["age"] = ["any"]
            elif "any" not in self.m_c["age"]:
                self.weight += self.num_of_ages - len(self.m_c["age"])
            if "status" not in self.m_c:
                self.m_c["status"] = ["any"]
            if "relationship_status" not in self.m_c:
                self.m_c["relationship_status"] = []
            else:
                self.weight += len(self.m_c["relationship_status"])
            if "skill" not in self.m_c:
                self.m_c["skill"] = []
            else:
                self.weight += self.num_of_skills - len(self.m_c["skill"])
            if "not_skill" not in self.m_c:
                self.m_c["not_skill"] = []
            else:
                self.weight += len(self.m_c["not_skill"])
            if "trait" not in self.m_c:
                self.m_c["trait"] = []
            else:
                self.weight += int((self.num_of_traits - len(self.m_c["trait"]) / 2))
            if "not_trait" not in self.m_c:
                self.m_c["not_trait"] = []
            else:
                self.weight += len(self.m_c["not_trait"])
            if "backstory" not in self.m_c:
                self.m_c["backstory"] = []
            else:
                self.weight += 1
            if "dies" not in self.m_c:
                self.m_c["dies"] = False
            if "gender" not in self.m_c:
                self.m_c["gender"] = []

        self.r_c = r_c if r_c else {}
        if self.r_c:
            if "age" not in self.r_c:
                self.r_c["age"] = ["any"]
            elif "any" not in self.r_c["age"]:
                self.weight += self.num_of_ages - len(self.r_c["age"])
            if "status" not in self.r_c:
                self.r_c["status"] = ["any"]
            if "relationship_status" not in self.r_c:
                self.r_c["relationship_status"] = []
            else:
                self.weight += len(self.r_c["relationship_status"])
            if "skill" not in self.r_c:
                self.r_c["skill"] = []
            else:
                self.weight += self.num_of_skills - len(self.r_c["skill"])
            if "not_skill" not in self.r_c:
                self.r_c["not_skill"] = []
            else:
                self.weight += len(self.r_c["not_skill"])
            if "trait" not in self.r_c:
                self.r_c["trait"] = []
            else:
                self.weight += int((self.num_of_traits - len(self.r_c["trait"]) / 2))
            if "not_trait" not in self.r_c:
                self.r_c["not_trait"] = []
            else:
                self.weight += len(self.r_c["not_trait"])
            if "backstory" not in self.r_c:
                self.r_c["backstory"] = []
            else:
                self.weight += 1
            if "dies" not in self.r_c:
                self.r_c["dies"] = False
            if "gender" not in self.r_c:
                self.r_c["gender"] = []

        self.new_cat = new_cat if new_cat else []
        self.exclude_involved = exclude_involved if exclude_involved else []
        self.injury = injury if injury else []
        self.history = history if history else []
        self.relationships = relationships if relationships else []
        self.outsider = outsider if outsider else {}
        if self.outsider:
            if "current_rep" not in self.outsider:
                self.outsider["current_rep"] = []
            if "changed" not in self.outsider:
                self.outsider["changed"] = 0
        self.other_clan = other_clan if other_clan else {}
        if self.other_clan:
            if "current_rep" not in self.other_clan:
                self.other_clan["current_rep"] = []
            elif "any" not in self.other_clan["current_rep"]:
                self.weight += (3 - len(self.other_clan["current_rep"])) * 5
            if "changed" not in self.other_clan:
                self.other_clan["changed"] = 0
        self.supplies = supplies if supplies else []
        self.new_gender = new_gender
        self.future_event = future_event if future_event else {}

    def __repr__(self):
        return f"{self.event_id} ({self.sub_type})"
