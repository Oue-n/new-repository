#!/usr/bin/env python
# coding: utf-8
# author: Taichi Hosoi

from __future__ import print_function, division  # pythonの3系と2系の互換性を持たせている

import aiwolfpy
import aiwolfpy.contentbuilder as cb  # aiwolfpyからプロトコルを生成する関数を流用

####################################################
# ┏━━┓
# ┃ ━┫
# ┣━┓┃
# ┗━━人村
import HeVillager as VillagerBehavior_5
import HeSeer as SeerBehavior_5
import HeWerewolf as WerewolfBehavior_5
import HePossessed as PossessedBehavior_5
####################################################

####################################################
# ┏━┳━━┓
# ┃ ┃ ━┫
# ┃ ┣━┓┃
# ┗━┻━人村
import HeVillager_15 as VillagerBehavior_15
import HeBodyguard_15 as BodyguardBehavior_15
import HeMedium_15 as MediumBehavior_15
import HeSeer_15 as SeerBehavior_15
import HeWerewolf_15 as WerewolfBehavior_15
import HePossessed_15 as PossessedBehavior_15
####################################################

# myname = 'HALUemon'  # サーバーにつなぐときの名前

class HALUemon(object):
    def __init__(self, agent_name):
        # myname
        self.myname = agent_name
        self.behavior = None

    def getName(self):  # mynameを返す
        return self.myname

    def initialize(self, base_info, diff_data, game_setting):  # ゲームの最初に呼び出すもの

        self.base_info = base_info  # 基本情報

        # game_setting
        self.game_setting = game_setting  # ゲーム設定
        self.remaining = len(base_info["remainTalkMap"])  # 過去トークの数？
        myRole = base_info["myRole"]  # 自分の役職

        if self.game_setting["playerNum"] == 5:  # 5人村用の設定
            if myRole == "VILLAGER":
                self.behavior = VillagerBehavior_5.VillagerBehavior(self.myname)
            elif myRole == "SEER":
                self.behavior = SeerBehavior_5.SeerBehavior(self.myname)
            elif myRole == "POSSESSED":
                self.behavior = PossessedBehavior_5.PossessedBehavior(self.myname)
            elif myRole == "WEREWOLF":
                self.behavior = WerewolfBehavior_5.WerewolfBehavior(self.myname)
            else:
                print("CAUTION: valid role not found, so chosen villager behav.")
                self.behavior = VillagerBehavior_5.VillagerBehavior(self.myname)

            self.behavior.initialize(base_info, diff_data, game_setting)
            print("=============INITIALIZE FINISHED============")
            # return

        elif self.game_setting["playerNum"] == 15:  # 15人村用の設定　人格を役職ごとに設定
            if myRole == "VILLAGER":
                self.behavior = VillagerBehavior_15.VillagerBehavior(self.myname)
            elif myRole == "MEDIUM":
                self.behavior = MediumBehavior_15.MediumBehavior(self.myname)
            elif myRole == "BODYGUARD":
                self.behavior = BodyguardBehavior_15.BodyguardBehavior(self.myname)
            elif myRole == "SEER":
                self.behavior = SeerBehavior_15.SeerBehavior(self.myname)
            elif myRole == "POSSESSED":
                self.behavior = PossessedBehavior_15.PossessedBehavior(self.myname)
            elif myRole == "WEREWOLF":
                self.behavior = WerewolfBehavior_15.WerewolfBehavior(self.myname)
            else:
                print("CAUTION: valid role not found, so chosen villager behav.")
                self.behavior = VillagerBehavior_15.VillagerBehavior(self.myname)

            self.behavior.initialize(base_info, diff_data, game_setting)  # 人格の初期化
            # print("=============INITIALIZE FINISHED============")

    def update(self, base_info, diff_data, request):  # 行動が行われるたびに呼び出される
        try:
            self.behavior.update(base_info, diff_data, request)  # 人格毎のupdateを呼び出す
        except Exception:
            pass

    def dayStart(self):  # 1日の初めに呼び出される
        try:
            self.behavior.dayStart()  # 人格ごとのdayStartを呼び出す
        except Exception:
            pass

    def talk(self):  # 発話内容をサーバーに渡すメソッド
        # return self.behavior.talk()
        try:
            return self.behavior.talk()  # 人格ごとに呼び出す
        except Exception:
            print("ERROR:maintalk")
            print(self.base_info["myRole"])
            return cb.over()  # エラーが起きたらoverを返す
        # return cb.over()

    def whisper(self):
        # return self.behavior.whisper()
        try:
            return self.behavior.whisper()  # 人格ごとに呼び出す
        except Exception:
            print("ERROR:mainwhisper")
            return cb.over()  # エラーが起きたらoverを返す

    def vote(self):
        # return self.behavior.vote()
        try:
            return self.behavior.vote()  # 人格ごとに呼び出す
        except Exception:
            print("ERROR:mainvote")
            print(self.base_info["myRole"])
            return 1  # エラーが起きたら1を返す

    def attack(self):
        # return self.behavior.attack()
        try:
            return self.behavior.attack()  # 人格ごとに呼び出す
        except Exception:
            print("ERROR:mainattack")
            return 1  # エラーが起きたら1を返す

    def divine(self):
        # return self.behavior.divine()
        try:
            return self.behavior.divine()  # 人格ごとに呼び出す
        except Exception:
            print("ERROR:maindivine")
            return 1  # エラーが起きたら1を返す

    def guard(self):
        # return self.behavior.guard()
        try:
            return self.behavior.guard()  # 人格ごとに呼び出す
        except Exception:
            print("ERROR:mainguard")
            return 1  # エラーが起きたら1を返す

    def finish(self):  # ゲーム終了時に呼び出されるメソッド
        return self.behavior.finish()  # 人格ごとに呼び出す

agent = HALUemon('HALUemon')

# run
if __name__ == '__main__':
    aiwolfpy.connect_parse(agent)

