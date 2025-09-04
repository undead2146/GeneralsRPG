
"""Compatibility shim: core character and charsheet moved to package `adventure.core`.

This module preserves the legacy import path `adventure.charsheet` by re-exporting
the public symbols from `adventure.core.character`.
"""

from adventure.core.character import *  # noqa: F401,F403

# Import specific classes needed for this module
try:
    from adventure.core.constants import HeroClasses
    from adventure.constants import Slot, Treasure
    from adventure.core.items import Item
    from redbot.core import commands
except ImportError:
    # Fallback for test environments
    class HeroClasses:
        @classmethod
        def from_name(cls, name):
            return None
    class Slot:
        two_handed = "two_handed"
    class Treasure:
        pass
    class Item:
        def __init__(self, **kwargs):
            pass
    class commands:
        class Context:
            pass


class Character:
    """An class to represent the characters stats."""

    def __init__(self, **kwargs):
        self._ctx: commands.Context = kwargs.pop("ctx")
        self.exp: int = kwargs.pop("exp")
        self.lvl: int = kwargs.pop("lvl")
        self.treasure: Treasure = kwargs.pop("treasure", Treasure())
        self.head: Item = kwargs.pop("head")
        self.neck: Item = kwargs.pop("neck")
        self.chest: Item = kwargs.pop("chest")
        self.gloves: Item = kwargs.pop("gloves")
        self.belt: Item = kwargs.pop("belt")
        self.legs: Item = kwargs.pop("legs")
        self.boots: Item = kwargs.pop("boots")
        self.left: Item = kwargs.pop("left")
        self.right: Item = kwargs.pop("right")
        self.ring: Item = kwargs.pop("ring")
        self.charm: Item = kwargs.pop("charm")
        self.backpack: dict = kwargs.pop("backpack")
        self.loadouts: dict = kwargs.pop("loadouts")
        self.heroclass: dict = kwargs.pop("heroclass")
        self.skill: dict = kwargs.pop("skill")
        self.bal: int = kwargs.pop("bal")
        self.user: discord.Member = kwargs.pop("user")
        self.sets = []
        self.rebirths = kwargs.pop("rebirths", 0)
        self.last_known_currency = kwargs.get("last_known_currency")
        self.last_currency_check = kwargs.get("last_currency_check")
        self.gear_set_bonus = {}
        self.get_set_bonus()
        self.maxlevel = self.get_max_level()
        self.lvl = self.lvl if self.lvl < self.maxlevel else self.maxlevel
        self.set_items = self.get_set_item_count()
        self.att, self._att = self.get_stat_value("att")
        self.cha, self._cha = self.get_stat_value("cha")
        self.int, self._int = self.get_stat_value("int")
        self.dex, self._dex = self.get_stat_value("dex")
        self.luck, self._luck = self.get_stat_value("luck")
        if self.lvl >= self.maxlevel and self.rebirths < 1:
            self.att = min(self.att, 5)
            self.cha = min(self.cha, 5)
            self.int = min(self.int, 5)
            self.dex = min(self.dex, 5)
            self.luck = min(self.luck, 5)
            self.skill["att"] = 1
            self.skill["int"] = 1
            self.skill["cha"] = 1
            self.skill["pool"] = 0
        self.total_att = self.att + self.skill["att"]
        self.total_int = self.int + self.skill["int"]
        self.total_cha = self.cha + self.skill["cha"]
        self.total_stats = self.total_att + self.total_int + self.total_cha + self.dex + self.luck
        self.remove_restrictions()
        self.adventures: dict = kwargs.pop("adventures")
        self.nega: dict = kwargs.pop("nega")
        self.weekly_score: dict = kwargs.pop("weekly_score")
        self.pieces_to_keep: dict = {
            "head": {},
            "neck": {},
            "chest": {},
            "gloves": {},
            "belt": {},
            "legs": {},
            "boots": {},
            "left": {},
            "right": {},
            "ring": {},
            "charm": {},
        }
        self.last_skill_reset: int = kwargs.pop("last_skill_reset", 0)
        self.daily_bonus = kwargs.pop(
            "daily_bonus_mapping", {"1": 0, "2": 0, "3": 0.5, "4": 0, "5": 0.5, "6": 1.0, "7": 1.0}
        )
        # Units persistence (unit-health / army state)
        self.units: dict = kwargs.pop("units", {})
        # Economy fields
        self.supplies: int = kwargs.pop("supplies", 0)
        self.command_points: int = kwargs.pop("command_points", 0)
        # optional repair kit counter (may also be represented as backpack items)
        self.repair_kits: int = kwargs.pop("repair_kits", 0)

    @property
    def hc(self) -> HeroClasses:
        return HeroClasses.from_name(self.heroclass["name"])

    def get_weapons(self) -> str:
        if self.left and self.left.slot is Slot.two_handed:
            return self.left.ansi
        elif self.right and self.right.slot is Slot.two_handed:
            return self.right.ansi
        elif self.left == self.right and self.left is not None:
            return self.left.ansi
        elif self.left is not None and self.right is None:
            return self.left.ansi
        elif self.right is not None and self.left is None:
            return self.right.ansi
        elif self.left is not None and self.right is not None:
            return humanize_list([self.right.ansi, self.left.ansi])
        return _("fists")

    def remove_restrictions(self):
        if self.hc is HeroClasses.ranger and self.heroclass["pet"]:
            requirements = (
                self._ctx.bot.get_cog("Adventure")
                .PETS.get(self.heroclass["pet"]["name"], {})
                .get("bonuses", {})
                .get("req", {})
            )
            if any(x in self.sets for x in ["The Supreme One", "Ainz Ooal Gown"]) and self.heroclass["pet"]["name"] in [
                "Albedo",
                "Rubedo",
                "Guardians of Nazarick",
            ]:
                return

            if self.heroclass["pet"]["cha"] > (self.total_cha + (self.total_int // 3) + (self.luck // 2)):
                self.heroclass["pet"] = {}
                return

            if requirements:
                if requirements.get("set") and requirements.get("set") not in self.sets:
                    self.heroclass["pet"] = {}

    def can_equip(self, item: Item):
        if self.user.id in DEV_LIST:
            return True
        return self.lvl >= self.equip_level(item)

    def equip_level(self, item: Item, rebirths=None):
        level = getattr(self, "rebirths", rebirths)
        return item.lvl if item.rarity is Rarities.event else max(item.lvl - min(max(level // 2 - 1, 0), 50), 1)

    def get_stat_value(self, stat: str):
        """Calculates the stats dynamically for each slot of equipment."""
        extrapoints = 0
        rebirths = copy(self.rebirths)
        extrapoints += rebirths // 10 * 5

        for _loop_counter in range(rebirths):
            if rebirths >= 30:
                extrapoints += 3
            elif rebirths >= 20:
                extrapoints += 5
            elif rebirths >= 10:
                extrapoints += 1
            elif rebirths < 10:
                extrapoints += 2
            rebirths -= 1

        extrapoints = int(extrapoints)

        stats = 0 + extrapoints
        for slot in Slot:
            if slot is Slot.two_handed:
                continue
            try:
                item = getattr(self, slot.name)
                if item:
                    stats += int(getattr(item, stat))
            except Exception as exc:
                log.error(f"error calculating {stat}", exc_info=exc)
        return (
            int(stats * self.gear_set_bonus.get("statmult", 1)) + self.gear_set_bonus.get(stat, 0),
            stats,
        )

    async def get_set_count(self, return_items: bool = False, set_name: str = None):
        set_names = {}
        returnable_items = []
        item_names = set()
        async for item in AsyncIter(self.backpack, steps=100):
            item = self.backpack[item]
            if item.rarity is not Rarities.set:
                continue
            if item.name in item_names:
                continue
            if not item.set:
                continue
            if set_name and set_name != item.set:
                continue
            if item.set and item.set not in set_names:
                returnable_items.append(item)
                item_names.add(item.name)
                set_names.update({item.set: (item.parts, 1)})
            elif item.set and item.set in set_names:
                returnable_items.append(item)
                item_names.add(item.name)
                parts, count = set_names[item.set]
                set_names[item.set] = (parts, count + 1)
        if return_items:
            return returnable_items
        for set_name in self._ctx.bot.get_cog("Adventure").SET_BONUSES:
            if set_name in set_names:
                continue
            set_names[set_name] = (
                max(bonus["parts"] for bonus in self._ctx.bot.get_cog("Adventure").SET_BONUSES[set_name]),
                0,
            )
        return set_names

    def get_set_bonus(self):
        set_names = {}
        last_slot = ""
        base = {
            "att": 0,
            "cha": 0,
            "int": 0,
            "dex": 0,
            "luck": 0,
            "statmult": 1,
            "xpmult": 1,
            "cpmult": 1,
        }
        added = []
        for slots in Slot:
            if slots is Slot.two_handed:
                continue
            if last_slot == "two handed":
                last_slot = slots
                continue
            item = getattr(self, slots.name)
            if item is None or item.name in added:
                continue
            if item.set and item.set not in set_names:
                added.append(item.name)
                set_names.update(
                    {item.set: (item.parts, 1, self._ctx.bot.get_cog("Adventure").SET_BONUSES.get(item.set, []))}
                )
            elif item.set and item.set in set_names:
                added.append(item.name)
                parts, count, bonus = set_names[item.set]
                set_names[item.set] = (parts, count + 1, bonus)
        full_sets = [(s, v[1]) for s, v in set_names.items() if v[1] >= v[0]]
        partial_sets = [(s, v[1]) for s, v in set_names.items()]
        self.sets = [s for s, _ in full_sets if s]
        for _set, parts in partial_sets:
            set_bonuses = self._ctx.bot.get_cog("Adventure").SET_BONUSES.get(_set, [])
            for bonus in set_bonuses:
                required_parts = bonus.get("parts", 100)
                if required_parts > parts:
                    continue
                for key, value in bonus.items():
                    if key == "parts":
                        continue
                    if key not in ["cpmult", "xpmult", "statmult"]:
                        base[key] += value
                    elif key in ["cpmult", "xpmult", "statmult"]:
                        if value > 1:
                            base[key] += value - 1
                        elif value >= 0:
                            base[key] -= 1 - value
        self.gear_set_bonus = base
        self.gear_set_bonus["cpmult"] = max(0, self.gear_set_bonus["cpmult"])
        self.gear_set_bonus["xpmult"] = max(0, self.gear_set_bonus["xpmult"])
        self.gear_set_bonus["statmult"] = max(-0.25, self.gear_set_bonus["statmult"])

    def __str__(self):
        """Define str to be our default look for the character sheet :thinkies:"""
        next_lvl = int((self.lvl + 1) ** 3.5)
        max_level_xp = int((self.maxlevel + 1) ** 3.5)
        hc = None
        if self.heroclass != {} and "name" in self.heroclass:
            hc = self.hc
            class_desc = self.hc.class_name + "\n\n" + self.hc.desc()
            if self.hc is HeroClasses.ranger:
                if not self.heroclass["pet"]:
                    class_desc += _("\n\n- Current pet: [None]")
                elif self.heroclass["pet"]:
                    if any(x in self.sets for x in ["The Supreme One", "Ainz Ooal Gown"]) and self.heroclass["pet"][
                        "name"
                    ] in [
                        "Albedo",
                        "Rubedo",
                        "Guardians of Nazarick",
                    ]:
                        class_desc += _("\n\n- Current servant: [{}]").format(self.heroclass["pet"]["name"])
                    else:
                        class_desc += _("\n\n- Current pet: [{}]").format(self.heroclass["pet"]["name"])
            class_desc = hc.class_colour.as_str(class_desc)
        else:
            class_desc = _("Hero.")

        daymult = self.daily_bonus.get(str(datetime.today().isoweekday()), 0)
        statmult = self.gear_set_bonus.get("statmult") - 1
        xpmult = (self.gear_set_bonus.get("xpmult") + daymult) - 1
        cpmult = (self.gear_set_bonus.get("cpmult") + daymult) - 1
        rebirth_text = "\n"
        if self.lvl >= self.maxlevel:
            rebirth_text = _(
                "You have reached max level. To continue gaining levels and xp, you will have to rebirth.\n\n"
            )
        return _(
            "{user}'s Character Sheet\n\n"
            "{{Rebirths: {rebirths}, \n Max Level: {maxlevel}}}\n"
            "{rebirth_text}"
            "A level {lvl} {class_desc} \n\n- "
            "ATTACK: {att} [+{att_skill}] - "
            "CHARISMA: {cha} [+{cha_skill}] - "
            "INTELLIGENCE: {int} [+{int_skill}]\n\n - "
            "DEXTERITY: {dex} - "
            "LUCK: {luck} \n\n- "
            "Backpack: {bp}/{bptotal} \n- "
            "Currency: {bal} \n- "
            "Experience: {xp}/{next_lvl} \n- "
            "Unspent skillpoints: {skill_points}\n\n"
            "Active bonus: {set_bonus}\n"
            "{daily}"
        ).format(
            user=self.user.display_name,
            rebirths=self.rebirths,
            lvl=self.lvl if self.lvl < self.maxlevel else self.maxlevel,
            rebirth_text=rebirth_text,
            maxlevel=self.maxlevel,
            class_desc=class_desc,
            att=humanize_number(self.att),
            att_skill=humanize_number(self.skill["att"]),
            int=humanize_number(self.int),
            int_skill=humanize_number(self.skill["int"]),
            cha=humanize_number(self.cha),
            cha_skill=humanize_number(self.skill["cha"]),
            dex=humanize_number(self.dex),
            luck=humanize_number(self.luck),
            bal=humanize_number(self.bal),
            xp=humanize_number(round(self.exp)),
            next_lvl=humanize_number(next_lvl) if self.lvl < self.maxlevel else humanize_number(max_level_xp),
            skill_points=0 if self.skill["pool"] < 0 else self.skill["pool"],
            set_bonus=(
                f"( {self.gear_set_bonus.get('att'):<2} | "
                f"{self.gear_set_bonus.get('cha'):<2} | "
                f"{self.gear_set_bonus.get('int'):<2} | "
                f"{self.gear_set_bonus.get('dex'):<2} | "
                f"{self.gear_set_bonus.get('luck'):<2} ) "
                f"Stats: {round(statmult * 100)}% | "
                f"EXP: {round(xpmult * 100)}% | "
                f"Credits: {round(cpmult * 100)}%"
            ),
            daily="" if daymult == 0 else _("* Daily bonus active"),
            bp=len(self.backpack),
            bptotal=self.get_backpack_slots(),
        )

    def get_equipment(self):
        """Define a secondary like __str__ to show our equipment."""
        form_string = ""
        last_slot = ""
        rjust = max([len(str(getattr(self, i.get_name(), 1))) for i in Slot if i is not Slot.two_handed])
        for slots in Slot:
            if slots is Slot.two_handed:
                continue
            if last_slot == "two handed":
                last_slot = slots
                continue
            item = getattr(self, slots.name)
            if item is None:
                last_slot = slots
                form_string += _("\n\n {} slot").format(slots.title())
                continue
            settext = ""
            slot_name = item.slot.get_name()
            form_string += _("\n\n {} slot").format(slot_name.title())
            last_slot = slot_name
            att = int(
                ((item.att * 2 if slot_name == "two handed" else item.att) * self.gear_set_bonus.get("statmult", 1))
            )
            inter = int(
                ((item.int * 2 if slot_name == "two handed" else item.int) * self.gear_set_bonus.get("statmult", 1))
            )
            cha = int(
                ((item.cha * 2 if slot_name == "two handed" else item.cha) * self.gear_set_bonus.get("statmult", 1))
            )
            dex = int(
                ((item.dex * 2 if slot_name == "two handed" else item.dex) * self.gear_set_bonus.get("statmult", 1))
            )
            luck = int(
                ((item.luck * 2 if slot_name == "two handed" else item.luck) * self.gear_set_bonus.get("statmult", 1))
            )
            att_space = " " if len(str(att)) >= 1 else ""
            cha_space = " " if len(str(cha)) >= 1 else ""
            int_space = " " if len(str(inter)) >= 1 else ""
            dex_space = " " if len(str(dex)) >= 1 else ""
            luck_space = " " if len(str(luck)) >= 1 else ""

            owned = ""
            if item.rarity in [Rarities.legendary, Rarities.event, Rarities.ascended] and item.degrade >= 0:
                owned += f" | [{item.degrade}#]"
            if item.set:
                settext += f" | Set `{item.set}` ({item.parts}pcs)"
            form_string += (
                f"\n{str(item):<{rjust}} - "
                f"({att_space}{att:<3} |"
                f"{cha_space}{cha:<3} |"
                f"{int_space}{inter:<3} |"
                f"{dex_space}{dex:<3} |"
                f"{luck_space}{luck:<3} )"
                f" | Lvl { self.equip_level(item):<5}"
                f"{owned}{settext}"
            )

        return form_string + "\n"

    def get_max_level(self) -> int:
        rebirths = max(self.rebirths, 0)

        if rebirths == 0:
            maxlevel = 5
        else:
            maxlevel = REBIRTH_LVL

        for _loop_counter in range(rebirths):
            if rebirths >= 20:
                maxlevel += REBIRTH_STEP
            elif rebirths > 10:
                maxlevel += 10
            elif rebirths <= 10:
                maxlevel += 5
            rebirths -= 1
        return min(maxlevel, 10000)

    @staticmethod
    def get_slot_index(slot: Slot):
        if slot not in [i for i in Slot]:
            return float("inf")
        return slot.order() or float("inf")

    @staticmethod
    def get_rarity_index(rarity: Rarities):
        if rarity not in [i for i in Rarities]:
            return float("inf")
        reverse_rarities = list(reversed(Rarities))
        return reverse_rarities.index(rarity)

    async def get_sorted_backpack(self, backpack: dict, slot: Optional[Slot] = None, rarity: Optional[Rarities] = None):
        tmp = {}

        def _sort(item):
            return self.get_rarity_index(item.rarity), item.lvl, item.total_stats

        async for item in AsyncIter(backpack, steps=100):
            slots = backpack[item].slot
            slot_name = slots.get_name()
            # if slots is Slot.two_handed:
            # slot_name = "two handed"
            if slot is not None and slots is not slot:
                continue
            if rarity is not None and rarity is not backpack[item].rarity:
                continue

            if slot_name not in tmp:
                tmp[slot_name] = []
            tmp[slot_name].append(backpack[item])
        slots = sorted(list(tmp.keys()), key=self.get_slot_index)
        final = []
        async for (idx, slot_name) in AsyncIter(slots, steps=100).enumerate():
            if tmp[slot_name]:
                final.append(sorted(tmp[slot_name], key=_sort))
        return final

    async def looted(self, how_many: int = 1, exclude: Optional[Set[Rarities]] = None) -> List[Tuple[str, int]]:
        if exclude is None:
            exclude = {Rarities.forged, Rarities.event}
        exclude.add(Rarities.forged)
        exclude.add(Rarities.event)
        items = [i for i in self.backpack.values() if i.rarity not in exclude]
        looted_so_far = 0
        looted = []
        if not items:
            return looted
        count = 0
        while how_many > looted_so_far:
            if looted_so_far >= how_many:
                break
            if count >= 10:
                # Our max items stolen is 10 now
                break
            item = random.choice(items)
            if not bool(random.getrandbits(1)):
                continue
            if item.name not in self.backpack:
                count += 1
                continue
            loot_number = random.randint(1, min(item.owned, how_many - looted_so_far))
            looted_so_far += loot_number
            looted.append((item.ansi, loot_number))
            item.owned -= loot_number
            if item.owned <= 0:
                del self.backpack[item.name]
            else:
                self.backpack[item.name] = item
        return looted

    async def make_backpack_tables(
        self, items: List[Item], title: str = "", show_delta: bool = False, include_total: bool = False
    ) -> List[BackpackTable]:
        table = BeautifulTable(default_alignment=ALIGN_CENTER, maxwidth=250)
        table.set_style(BeautifulTable.STYLE_RST)
        table.border.top = ""
        table.border.bottom = ""
        tables = []
        items_group = []
        headers = [
            # "Name",
            # "Slot",
            "ATT",
            "CHA",
            "INT",
            "DEX",
            "LUCK",
            # "LVL",
            # "QTY",
            # "DEG",
            # "SET",
        ]
        # table.columns.header = headers
        headertable = BeautifulTable(default_alignment=ALIGN_CENTER, maxwidth=250)
        headertable.set_style(BeautifulTable.STYLE_RST)
        # subtable.rows.append(["Name"])
        headertable.columns.width = COLUMN_WIDTHS
        headertable.rows.append(headers)
        headertable.border.top = ""
        # table.rows.append(["Name"])
        table.rows.append([headertable])
        # used for displaying the "headers"

        footer = _("\nPage {page_num}").format(page_num=len(tables) + 1)
        att = 0
        cha = 0
        intel = 0
        dex = 0
        luck = 0
        for item in items:
            footer = _("\nPage {page_num}").format(page_num=len(tables) + 1)
            item_name, item_row = item.row(self, show_delta=show_delta)
            items_group.append(item)
            table.rows.append([item_name])
            table.rows.append([item_row])
            if len(title + str(table) + footer) > 1600:
                table.rows.pop()
                table.rows.pop()
                items_group.pop()
                if include_total:
                    totaltable = BeautifulTable(default_alignment=ALIGN_CENTER, maxwidth=250)
                    totaltable.set_style(BeautifulTable.STYLE_RST)
                    totaltable.columns.width = COLUMN_WIDTHS
                    totaltable.rows.append([att, cha, intel, dex, luck])
                    # used when the total is to be included at the bottom
                    table.rows.append([_("Total")])
                    table.rows.append([totaltable])
                att = 0
                cha = 0
                intel = 0
                dex = 0
                luck = 0

                tables.append(BackpackTable(table=box(f"{title}\n{table} {footer}", lang="ansi"), items=items_group))
                items_group = []
                table = BeautifulTable(default_alignment=ALIGN_CENTER, maxwidth=250)
                table.set_style(BeautifulTable.STYLE_RST)
                table.border.top = ""
                table.border.bottom = ""
                table.rows.append([headertable])
                # table.columns.header = headers
                table.rows.append([item_name])
                table.rows.append([item_row])
                items_group.append(item)
            att += item.att * (1 if item.slot is not Slot.two_handed else 2)
            cha += item.cha * (1 if item.slot is not Slot.two_handed else 2)
            intel += item.int * (1 if item.slot is not Slot.two_handed else 2)
            dex += item.dex * (1 if item.slot is not Slot.two_handed else 2)
            luck += item.luck * (1 if item.slot is not Slot.two_handed else 2)
        if include_total:
            totaltable = BeautifulTable(default_alignment=ALIGN_CENTER, maxwidth=250)
            totaltable.set_style(BeautifulTable.STYLE_RST)
            totaltable.columns.width = COLUMN_WIDTHS
            totaltable.rows.append([att, cha, intel, dex, luck])
            table.rows.append([_("Total")])
            table.rows.append([totaltable])
        tables.append(BackpackTable(table=box(f"{title}\n{table} {footer}", lang="ansi"), items=items_group))
        return tables

    async def get_backpack(
        self,
        forging: bool = False,
        consumed=None,
        rarity: Optional[Rarities] = None,
        slot: Optional[Slot] = None,
        show_delta=False,
        equippable=False,
        set_name: Optional[str] = None,
        clean: bool = False,
    ):
        if consumed is None:
            consumed = []
        bkpk = await self.get_sorted_backpack(self.backpack, slot=slot, rarity=rarity)
        consumed_list = consumed
        rows = []
        if not forging:
            msg = _("{author}'s backpack\n\n").format(author=escape(self.user.display_name, formatting=True))
        else:
            msg = _("{author}'s forgeables\n\n").format(author=escape(self.user.display_name, formatting=True))
        # subtable = BeautifulTable(default_alignment=ALIGN_CENTER, maxwidth=250)
        async for slot_group in AsyncIter(bkpk, steps=100):
            slot_name_org = slot_group[0].slot
            if slot is not None and slot is not slot_name_org:
                continue
            if clean and not slot_group:
                continue
            async for item in AsyncIter(slot_group, steps=100):
                if forging and (item.rarity in [Rarities.forged, Rarities.set] or item in consumed_list):
                    continue
                if forging and item.rarity is Rarities.ascended:
                    if self.rebirths < 30:
                        continue
                if rarity is not None and rarity is not item.rarity:
                    continue
                if equippable and not self.can_equip(item):
                    continue
                if set_name is not None and set_name != item.set:
                    continue
                rows.append(item)
        return await self.make_backpack_tables(rows, msg, show_delta)

    async def get_sorted_backpack_arg_parse(
        self,
        backpack: dict,
        slots: List[Slot],
        rarities: List[Rarities],
        sets: List[str],
        equippable: bool,
        _except: bool,
        strength: MutableMapping[str, Any],
        intelligence: MutableMapping[str, Any],
        charisma: MutableMapping[str, Any],
        luck: MutableMapping[str, Any],
        dexterity: MutableMapping[str, Any],
        level: MutableMapping[str, Any],
        degrade: MutableMapping[str, Any],
        ignore_case: bool,
        match: Optional[str],
        no_match: Optional[str],
        rarity_exclude: List[str] = None,
    ):
        tmp = {}

        def _sort(item):
            return self.get_rarity_index(item.rarity), item.lvl, item.total_stats

        if not _except:
            async for item_name in AsyncIter(backpack, steps=100):
                item = backpack[item_name]
                item_slots = item.slot
                slot_name = item_slots.get_name()
                mult = 2 if item.slot is Slot.two_handed else 1
                if rarity_exclude is not None and item.rarity.name in rarity_exclude:
                    continue

                if no_match:
                    actual_item_name = str(item)
                    if ignore_case:
                        if no_match.lower() in actual_item_name.lower():
                            continue
                    elif no_match in actual_item_name:
                        continue
                if match:
                    actual_item_name = str(item)
                    if ignore_case:
                        if match.lower() not in actual_item_name.lower():
                            continue
                    elif match not in actual_item_name:
                        continue
                if slots and item_slots not in slots:
                    continue
                if sets and item.rarity is not Rarities.set:
                    continue
                elif rarities and item.rarity not in rarities:
                    continue
                if sets and item.set not in sets:
                    continue
                e_level = self.equip_level(item)
                if equippable and self.lvl < e_level:
                    continue
                if degrade and item.rarity in [Rarities.legendary, Rarities.ascended, Rarities.event]:
                    if (d := degrade.get("equal")) is not None:
                        if item.degrade != d:
                            continue
                    elif not degrade["min"] < item.degrade < degrade["max"]:
                        continue
                if level:
                    if (d := level.get("equal")) is not None:
                        if item.lvl != d:
                            continue
                    elif not level["min"] < item.lvl < level["max"]:
                        continue
                if dexterity:
                    if (d := dexterity.get("equal")) is not None:
                        if item.dex * mult != d:
                            continue
                    elif not dexterity["min"] < item.dex * mult < dexterity["max"]:
                        continue
                if luck:
                    if (d := luck.get("equal")) is not None:
                        if item.luck * mult != d:
                            continue
                    elif not luck["min"] < item.luck * mult < luck["max"]:
                        continue
                if charisma:
                    if (d := charisma.get("equal")) is not None:
                        if item.cha * mult != d:
                            continue
                    elif not charisma["min"] < item.cha * mult < charisma["max"]:
                        continue
                if intelligence:
                    if (d := intelligence.get("equal")) is not None:
                        if item.int * mult != d:
                            continue
                    elif not intelligence["min"] < item.int * mult < intelligence["max"]:
                        continue
                if strength:
                    if (d := strength.get("equal")) is not None:
                        if item.att * mult != d:
                            continue
                    elif not strength["min"] < item.att * mult <= strength["max"]:
                        continue

                if slot_name not in tmp:
                    tmp[slot_name] = []
                tmp[slot_name].append(item)
        else:
            rarities = [] if rarities == [i for i in Rarities] else rarities
            slots = [] if slots == [i for i in Slot] else slots
            async for item_name in AsyncIter(backpack, steps=100):
                item = backpack[item_name]
                item_slots = item.slot
                slot_name = item_slots.get_name()
                mult = 2 if item.slot is Slot.two_handed else 1
                if rarity_exclude is not None and item.rarity in rarity_exclude:
                    continue

                if no_match:
                    actual_item_name = str(item)
                    if ignore_case:
                        if no_match.lower() not in actual_item_name.lower():
                            continue
                    elif no_match not in actual_item_name:
                        continue
                if match:
                    actual_item_name = str(item)
                    if ignore_case:
                        if match.lower() in actual_item_name.lower():
                            continue
                    elif match in actual_item_name:
                        continue
                if slots and item_slots in slots:
                    continue
                elif rarities and item.rarity in rarities:
                    continue
                if sets and item.set in sets:
                    continue
                e_level = self.equip_level(item)
                if equippable and self.lvl >= e_level:
                    continue
                if degrade and item.rarity in [Rarities.legendary, Rarities.ascended, Rarities.event]:
                    if (d := degrade.get("equal")) is not None:
                        if item.degrade == d:
                            continue
                    elif degrade["min"] < item.degrade < degrade["max"]:
                        continue
                if level:
                    if (d := level.get("equal")) is not None:
                        if item.lvl == d:
                            continue
                    elif level["min"] < item.lvl < level["max"]:
                        continue
                if dexterity:
                    if (d := dexterity.get("equal")) is not None:
                        if item.dex * mult == d:
                            continue
                    elif dexterity["min"] < item.dex * mult < dexterity["max"]:
                        continue
                if luck:
                    if (d := luck.get("equal")) is not None:
                        if item.luck * mult == d:
                            continue
                    elif luck["min"] < item.luck * mult < luck["max"]:
                        continue
                if charisma:
                    if (d := charisma.get("equal")) is not None:
                        if item.cha * mult == d:
                            continue
                    elif charisma["min"] < item.cha * mult < charisma["max"]:
                        continue
                if intelligence:
                    if (d := intelligence.get("equal")) is not None:
                        if item.int * mult == d:
                            continue
                    elif intelligence["min"] < item.int * mult < intelligence["max"]:
                        continue
                if strength:
                    if (d := strength.get("equal")) is not None:
                        if item.att * mult == d:
                            continue
                    elif strength["min"] < item.att * mult <= strength["max"]:
                        continue
                if slot_name not in tmp:
                    tmp[slot_name] = []
                tmp[slot_name].append(item)

        slots = sorted(list(tmp.keys()), key=self.get_slot_index)
        final = []
        async for (idx, slot_name) in AsyncIter(slots, steps=100).enumerate():
            if tmp[slot_name]:
                final.append((slot_name, sorted(tmp[slot_name], key=_sort)))
        return final

    async def get_argparse_backpack(self, query: MutableMapping[str, Any]) -> List[str]:
        delta = query.pop("delta", False)
        equippable = query.pop("equippable", False)
        sets = query.pop("set", [])
        rarities = query.pop("rarity", [])
        slots = query.pop("slot", [])
        strength = query.pop("strength", {})
        intelligence = query.pop("intelligence", {})
        charisma = query.pop("charisma", {})
        luck = query.pop("luck", {})
        dexterity = query.pop("dexterity", {})
        level = query.pop("level", {})
        degrade = query.pop("degrade", {})
        ignore_case = query.pop("icase", False)
        match = query.pop("match", None)
        no_match = query.pop("no_match", None)
        _except = query.pop("except", False)

        bkpk = await self.get_sorted_backpack_arg_parse(
            self.backpack,
            slots=slots,
            rarities=rarities,
            sets=sets,
            equippable=equippable,
            strength=strength,
            intelligence=intelligence,
            charisma=charisma,
            luck=luck,
            dexterity=dexterity,
            level=level,
            degrade=degrade,
            match=match,
            no_match=no_match,
            ignore_case=ignore_case,
            _except=_except,
        )
        items = [item for groups in bkpk for item in groups[1]]
        return await self.make_backpack_tables(items, show_delta=delta)

    async def get_argparse_backpack_items(
        self, query: MutableMapping[str, Any], rarity_exclude: List[str] = None
    ) -> List[Item]:
        equippable = query.pop("equippable", False)
        sets = query.pop("set", [])
        rarities = query.pop("rarity", [])
        slots = query.pop("slot", [])
        strength = query.pop("strength", {})
        intelligence = query.pop("intelligence", {})
        charisma = query.pop("charisma", {})
        luck = query.pop("luck", {})
        dexterity = query.pop("dexterity", {})
        level = query.pop("level", {})
        degrade = query.pop("degrade", {})
        ignore_case = query.pop("icase", False)
        match = query.pop("match", None)
        no_match = query.pop("no_match", None)
        _except = query.pop("except", False)

        bkpk = await self.get_sorted_backpack_arg_parse(
            self.backpack,
            slots=slots,
            rarities=rarities,
            sets=sets,
            equippable=equippable,
            strength=strength,
            intelligence=intelligence,
            charisma=charisma,
            luck=luck,
            dexterity=dexterity,
            level=level,
            degrade=degrade,
            match=match,
            no_match=no_match,
            ignore_case=ignore_case,
            _except=_except,
        )
        return bkpk

    def get_equipped_delta(self, equiped: Optional[Item], to_compare: Optional[Item], stat_name: str) -> str:
        if (equiped and equiped.slot is Slot.two_handed) and (to_compare and to_compare.slot is Slot.two_handed):
            equipped_stat = getattr(equiped, stat_name, 0) * 2
            comparing_to_stat = getattr(to_compare, stat_name, 0) * 2
        elif to_compare and to_compare.slot is Slot.two_handed:
            equipped_left_stat = getattr(self.left, stat_name, 0)
            equipped_right_stat = getattr(self.right, stat_name, 0)
            equipped_stat = equipped_left_stat + equipped_right_stat
            comparing_to_stat = getattr(to_compare, stat_name, 0) * 2
        elif (equiped and equiped.slot is Slot.two_handed) and (to_compare and to_compare.slot is not Slot.two_handed):
            equipped_stat = getattr(equiped, stat_name, 0) * 2
            comparing_to_stat = getattr(to_compare, stat_name, 0)
        else:
            equipped_stat = getattr(equiped, stat_name, 0)
            comparing_to_stat = getattr(to_compare, stat_name, 0)

        diff = int(comparing_to_stat - equipped_stat)
        return ANSITextColours.red.as_str(diff) if diff < 0 else ANSITextColours.green.as_str(diff) if diff > 0 else "0"

    async def equip_item(self, item: Item, from_backpack: bool = True, dev=False):
        """This handles moving an item from backpack to equipment."""
        equiplevel = self.equip_level(item)
        if equiplevel > self.lvl:
            if not dev:
                if not from_backpack:
                    await self.add_to_backpack(item)
                return self
        if from_backpack and item.name in self.backpack:
            if self.backpack[item.name].owned > 1:
                self.backpack[item.name].owned -= 1
            else:
                del self.backpack[item.name]
        if item.slot is not Slot.two_handed:
            current = getattr(self, item.slot.name)
            if current:
                await self.unequip_item(current)
            setattr(self, item.slot.name, item)
        else:
            slots = [getattr(self, "left"), getattr(self, "right")]
            for slot in slots:
                if slot:
                    await self.unequip_item(slot)
            setattr(self, "left", item)
            setattr(self, "right", item)
        return self

    def get_backpack_slots(self, is_dev: bool = False):
        if is_dev:
            return "N/A"
        else:
            return humanize_number((50 + (self.rebirths * 5)))

    def is_backpack_full(self, is_dev: bool = False):
        if is_dev:
            return False
        return len(self.backpack) > (50 + (self.rebirths * 5))

    async def add_to_backpack(self, item: Item, number: int = 1):
        if item:
            if item.name in self.backpack:
                self.backpack[item.name].owned += number
            else:
                self.backpack[item.name] = item

    async def add_supplies(self, amount: int):
        try:
            self.supplies += int(amount)
        except Exception:
            self.supplies += 0
        return self.supplies

    async def add_cp(self, amount: int):
        try:
            self.command_points += int(amount)
        except Exception:
            self.command_points += 0
        return self.command_points

    async def equip_loadout(self, loadout_name):
        loadout = self.loadouts[loadout_name]
        for slot, item in loadout.items():
            name_unformatted = "".join(item.keys())
            name = Item.remove_markdowns(name_unformatted)
            current = getattr(self, slot)
            if current and current.name == name_unformatted:
                continue
            if current and current.name != name_unformatted:
                await self.unequip_item(current)
            if name not in self.backpack:
                setattr(self, slot, None)
            else:
                if item.get("rarity", "common") == "event":
                    equiplevel = item.get(
                        "lvl",
                        max((item.get("lvl", 1) - min(max(self.rebirths // 2 - 1, 0), 50)), 1),
                    )
                else:
                    equiplevel = max((item.get("lvl", 1) - min(max(self.rebirths // 2 - 1, 0), 50)), 1)
                if equiplevel > self.lvl:
                    continue

                await self.equip_item(self.backpack[name], True)

        return self

    @staticmethod
    async def save_loadout(char):
        """Return a dict of currently equipped items for loadouts."""
        return {
            "head": char.head.to_json() if char.head else {},
            "neck": char.neck.to_json() if char.neck else {},
            "chest": char.chest.to_json() if char.chest else {},
            "gloves": char.gloves.to_json() if char.gloves else {},
            "belt": char.belt.to_json() if char.belt else {},
            "legs": char.legs.to_json() if char.legs else {},
            "boots": char.boots.to_json() if char.boots else {},
            "left": char.left.to_json() if char.left else {},
            "right": char.right.to_json() if char.right else {},
            "ring": char.ring.to_json() if char.ring else {},
            "charm": char.charm.to_json() if char.charm else {},
        }

    def get_current_equipment(self, return_place_holder: bool = False) -> List[Item]:
        """returns a list of Items currently equipped."""
        equipped = []
        for slot in Slot:
            if slot is Slot.two_handed:
                continue
            item = getattr(self, slot.name)
            if item:
                equipped.append(item)
            elif return_place_holder:
                equipped.append(get_place_holder(self._ctx, slot))
        return equipped

    async def unequip_item(self, item: Item):
        """This handles moving an item equipment to backpack."""
        if item.name in self.backpack:
            self.backpack[item.name].owned += 1
        else:
            self.backpack[item.name] = item
        if item.slot is not Slot.two_handed:
            setattr(self, item.slot.name, None)
        else:
            setattr(self, "left", None)
            setattr(self, "right", None)
        return self

    @classmethod
    async def from_json(
        cls,
        ctx: commands.Context,
        config: Config,
        user: Union[discord.Member, discord.User],
        daily_bonus_mapping: Dict[str, float],
    ):
        """Return a Character object from config and user."""
        data = await config.user(user).all()
        try:
            balance = await bank.get_balance(user)
        except Exception:
            balance = 0
        equipment = {k: Item.from_json(ctx, v) if v else None for k, v in data["items"].items() if k != "backpack"}
        if "int" not in data["skill"]:
            data["skill"]["int"] = 0
            # auto update old users with new skill slot
            # likely unnecessary since this worked without it but this prevents
            # potential issues
        loadouts = data["loadouts"]
        heroclass = {
            "name": "Hero",
            "ability": False,
            "desc": "Your basic adventuring hero.",
            "cooldown": 0,
        }
        if "class" in data:
            # to move from old data to new data
            heroclass = data["class"]
        if "heroclass" in data:
            # we're saving to new data to avoid keyword conflicts
            heroclass = data["heroclass"]
        if "backpack" not in data:
            # helps move old data to new format
            backpack = {}
            for n, i in data["items"]["backpack"].items():
                item = Item.from_json(ctx, {n: i})
                backpack[item.name] = item
        else:
            backpack = {n: Item.from_json(ctx, {n: i}) for n, i in data["backpack"].items()}
        while len(data["treasure"]) < 5:
            data["treasure"].append(0)

        if len(data["treasure"]) == 5:
            data["treasure"].insert(4, 0)

        if heroclass["name"].lower() == "ranger":
            if heroclass.get("pet"):
                theme = await config.theme()
                extra_pets = await config.themes.all()
                extra_pets = extra_pets.get(theme, {}).get("pets", {})
                pet_list = {**ctx.bot.get_cog("Adventure").PETS, **extra_pets}
                heroclass["pet"] = pet_list.get(heroclass["pet"]["name"], heroclass["pet"])

        if "adventures" in data:
            adventures = data["adventures"]
        else:
            adventures = {
                "wins": 0,
                "loses": 0,
                "fight": 0,
                "spell": 0,
                "talk": 0,
                "pray": 0,
                "run": 0,
                "fumbles": 0,
            }
        if "nega" in data:
            nega = data["nega"]
        else:
            nega = {
                "wins": 0,
                "loses": 0,
                "xp__earnings": 0,
                "gold__losses": 0,
            }
        current_week = date.today().isocalendar()[1]
        if "weekly_score" in data and data["weekly_score"]["week"] >= current_week:
            weekly = data["weekly_score"]
        else:
            weekly = {"adventures": 0, "rebirths": 0, "week": current_week}

        hero_data = {
            "adventures": adventures,
            "nega": nega,
            "weekly_score": weekly,
            "exp": max(data["exp"], 0),
            "lvl": data["lvl"],
            "att": data["att"],
            "int": data["int"],
            "cha": data["cha"],
            "treasure": Treasure(*data["treasure"]),
            "backpack": backpack,
            "loadouts": loadouts,
            "heroclass": heroclass,
            "skill": data["skill"],
            "bal": balance,
            "user": user,
            "rebirths": data.pop("rebirths", 0),
            "set_items": data.get("set_items", 0),
            "units": data.get("units", {}),
            "supplies": data.get("supplies", 0),
            "command_points": data.get("command_points", 0),
        }
        for k, v in equipment.items():
            hero_data[k] = v
        hero_data["last_skill_reset"] = data.get("last_skill_reset", 0)
        hero_data["last_known_currency"] = data.get("last_known_currency", 0)
        hero_data["last_currency_check"] = data.get("last_currency_check", 0)
        return cls(**hero_data, ctx=ctx, daily_bonus_mapping=daily_bonus_mapping)

    def get_set_item_count(self):
        count_set = 0
        last_slot = ""
        for slots in Slot:
            if slots is Slot.two_handed:
                continue
            if last_slot == "two handed":
                last_slot = slots
                continue
            item = getattr(self, slots.name)
            if item is None:
                continue
            if item.rarity in [Rarities.set]:
                count_set += 1
        for k, v in self.backpack.items():
            for n, i in v.to_json().items():
                if i.get("rarity", False) in ["set"]:
                    count_set += v.owned
        return count_set

    async def to_json(self, ctx: commands.Context, config: Config) -> dict:
        backpack = {}
        for k, v in self.backpack.items():
            for n, i in v.to_json().items():
                backpack[n] = i

        if self.hc is HeroClasses.ranger and self.heroclass.get("pet"):
            theme = await config.theme()
            extra_pets = await config.themes.all()
            extra_pets = extra_pets.get(theme, {}).get("pets", {})
            pet_list = {**ctx.bot.get_cog("Adventure").PETS, **extra_pets}
            self.heroclass["pet"] = pet_list.get(self.heroclass["pet"]["name"], self.heroclass["pet"])

        return {
            "adventures": self.adventures,
            "nega": self.nega,
            "weekly_score": self.weekly_score,
            "exp": self.exp,
            "lvl": self.lvl,
            "att": self._att,
            "int": self._int,
            "cha": self._cha,
            "treasure": self.treasure.to_json(),
            "items": {
                "head": self.head.to_json() if self.head else {},
                "neck": self.neck.to_json() if self.neck else {},
                "chest": self.chest.to_json() if self.chest else {},
                "gloves": self.gloves.to_json() if self.gloves else {},
                "belt": self.belt.to_json() if self.belt else {},
                "legs": self.legs.to_json() if self.legs else {},
                "boots": self.boots.to_json() if self.boots else {},
                "left": self.left.to_json() if self.left else {},
                "right": self.right.to_json() if self.right else {},
                "ring": self.ring.to_json() if self.ring else {},
                "charm": self.charm.to_json() if self.charm else {},
            },
            "backpack": backpack,
            "units": self.units,
            "loadouts": self.loadouts,  # convert to dict of items
            "heroclass": self.heroclass,
            "skill": self.skill,
            "rebirths": self.rebirths,
            "set_items": self.set_items,
            "last_skill_reset": self.last_skill_reset,
            "last_known_currency": self.last_known_currency,
            "supplies": self.supplies,
            "command_points": self.command_points,
        }

    async def rebirth(self, dev_val: int = None) -> dict:
        if dev_val is None:
            self.rebirths += 1
        else:
            self.rebirths = dev_val
        self.keep_equipped()
        backpack = {}
        for item in [
            self.head,
            self.chest,
            self.gloves,
            self.belt,
            self.legs,
            self.boots,
            self.ring,
            self.charm,
            self.neck,
        ]:
            if item and item.to_json() not in list(self.pieces_to_keep.values()):
                await self.add_to_backpack(item)
        if (self.left and self.left.slot is Slot.two_handed) or (self.right and self.right.slot is Slot.two_handed):
            if self.left and self.left.to_json() not in list(self.pieces_to_keep.values()):
                await self.add_to_backpack(self.left)
            elif self.right and self.right.to_json() not in list(self.pieces_to_keep.values()):
                await self.add_to_backpack(self.right)
        else:
            for item in [self.left, self.right]:
                if item and item.to_json() not in list(self.pieces_to_keep.values()):
                    await self.add_to_backpack(item)
        forged = 0
        for k, v in self.backpack.items():
            for n, i in v.to_json().items():
                if i.get("degrade", 0) == -1 and i.get("rarity", "common") == "event":
                    backpack[n] = i
                elif i.get("rarity", False) in ["set", "forged"] or str(v) in [".mirror_shield"]:
                    if i.get("rarity", False) in ["forged"]:
                        if forged > 0:
                            continue
                        forged += 1
                    backpack[n] = i
                elif self.rebirths < 50 and i.get("rarity", False) in ["legendary", "event", "ascended"]:
                    if "degrade" in i:
                        i["degrade"] -= 1
                        if i.get("degrade", 0) >= 0:
                            backpack[n] = i

        tresure = Treasure()
        if self.rebirths >= 15:
            tresure.legendary += max(int(self.rebirths // 15), 0)
        if self.rebirths >= 10:
            tresure.epic += max(int(self.rebirths // 10), 0)
        if self.rebirths >= 5:
            tresure.rare += max(int(self.rebirths // 5), 0)
        if self.rebirths > 0:
            tresure.normal += max(int(self.rebirths), 0)

        self.weekly_score.update({"rebirths": self.weekly_score.get("rebirths", 0) + 1})
        self.heroclass["cooldown"] = time.time() + 60  # Set skill cooldown to 60s from rebirth
        return {
            "adventures": self.adventures,
            "nega": self.nega,
            "weekly_score": self.weekly_score,
            "exp": 0,
            "lvl": 1,
            "att": 0,
            "int": 0,
            "cha": 0,
            "treasure": tresure.to_json(),
            "items": {
                "head": self.pieces_to_keep.get("head", {}),
                "neck": self.pieces_to_keep.get("neck", {}),
                "chest": self.pieces_to_keep.get("chest", {}),
                "gloves": self.pieces_to_keep.get("gloves", {}),
                "belt": self.pieces_to_keep.get("belt", {}),
                "legs": self.pieces_to_keep.get("legs", {}),
                "boots": self.pieces_to_keep.get("boots", {}),
                "left": self.pieces_to_keep.get("left", {}),
                "right": self.pieces_to_keep.get("right", {}),
                "ring": self.pieces_to_keep.get("ring", {}),
                "charm": self.pieces_to_keep.get("charm", {}),
            },
            "backpack": backpack,
            "loadouts": self.loadouts,  # convert to dict of items
            "heroclass": self.heroclass,
            "skill": {"pool": 0, "att": 0, "cha": 0, "int": 0},
            "rebirths": self.rebirths,
            "set_items": self.set_items,
            "last_known_currency": 0,
            "last_currency_check": 0,
        }

    def keep_equipped(self):
        items_to_keep = {}
        for slots in Slot:
            if slots in [Slot.two_handed, Slot.left, Slot.right]:
                continue
            items_to_keep[slots.name] = {}
            item = getattr(self, slots.name)
            if item and item.set and self.rebirths >= 30:
                items_to_keep[slots.name] = item.to_json()
        if self.left == self.right and self.right is not None and self.left is not None:
            if self.right.set and self.rebirths >= 30:
                items_to_keep["right"] = self.right.to_json()
                items_to_keep["left"] = self.left.to_json()
        else:
            if self.left and self.left.set and self.rebirths >= 30:
                items_to_keep["left"] = self.left.to_json()
            if self.right and self.right.set and self.rebirths >= 30:
                items_to_keep["right"] = self.right.to_json()
        self.pieces_to_keep = items_to_keep


async def calculate_sp(lvl_end: int, c: Character):
    points_300 = lvl_end - 300 if lvl_end >= 300 else 0
    points_200 = (lvl_end - 200) - points_300 if lvl_end >= 200 else 0
    points_100 = (lvl_end - 100) - points_300 - points_200 if lvl_end >= 100 else 0
    points_0 = lvl_end - points_100 - points_300 - points_200
    if 200 <= lvl_end < 300:
        points_200 += 1
        points_0 -= 1
    points = (c.rebirths * 10) + (points_300 * 1) + (points_200 * 5) + (points_100 * 1) + (points_0 * 0.5)

    return int(points)


def has_funds_check(cost):
    async def predicate(ctx):
        if not await bank.can_spend(ctx.author, cost):
            currency_name = await bank.get_currency_name(ctx.guild)
            raise commands.CheckFailure(
                _("You need {cost} {currency_name} to be able to take parts in an adventures").format(
                    cost=humanize_number(cost), currency_name=currency_name
                )
            )
        return True

    return check(predicate)


async def has_funds(user, cost):
    return await bank.can_spend(user, cost)


def get_place_holder(ctx, slot: Slot) -> Item:
    return Item(
        ctx=ctx,
        name="Empty Slot",
        slot=slot.to_json(),
        rarity="N/A",
        att=0,
        int=0,
        cha=0,
        dex=0,
        luck=0,
        owned=0,
        parts=0,
    )
