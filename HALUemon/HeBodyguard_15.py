#!/usr/bin/env python
# coding: utf-8
# author: HALU Taichi Hosoi
# Bodyguard 15 sub class
# ┏━┳━━┓
# ┃ ┃ ━┫
# ┃ ┣━┓┃
# ┗━┻━人村

import HeVillager_15 as VillagerBehavior
import random

class BodyguardBehavior(VillagerBehavior.VillagerBehavior):  # ()にいれることで村人人格のサブクラスにしている
    """
    狩人の振る舞い
    """

    def __init__(self, agent_name):
        super().__init__(agent_name)

    def initialize(self, base_info, diff_data, game_setting):
        super().initialize(base_info, diff_data, game_setting)
        # self.result_guard = set()      # 護衛成功したエージェントの集合、villagerに移動したのでコメントアウト
        self.ated_players_num = 0      # 前日までの襲撃された人数を覚えておく変数(int)
        self.guarded_player = 0        # 夜に誰を護衛したかを覚えておく変数(int)

        # 護衛記録の更新方法について
        # initializeで初期化
        # guardでエージェントナンバーをguarded_playerに入れる
        # talkの1ターン目に、
        #   前日より襲撃結果が増えていたら、何もしない
        #   前日より襲撃結果が増えていなかったら、guarded_playerに入っているエージェントナンバーをresult_guardに追加
        #   その後、guarded_playerを0に変更
        #   襲撃された人数は、ated_players_numに格納して次の日にまた確認

        # result_guardに入ってるエージェントは自分目線確定白になる
        # result_guardに入ってるエージェントに黒だししてるdivinedersがいたら、likely_fake_divinedersに入れる

        # likely_fake_divineders (狩人) の更新
        # 自分へ黒だしした占い師と、護衛成功した人に黒だしした占い師は、自分目線確定偽占い師になる
        for CO_seer in list(self.divineders - self.fake_divineders):
            if int(self.base_info['agentIdx']) in self.result_all_divineders[CO_seer]["black"]:
                self.likely_fake_divineders.add(CO_seer)
            if self.result_guard & self.result_all_divineders[CO_seer]["black"]:
                self.likely_fake_divineders.add(CO_seer)

    def update(self, base_info, diff_data, request):
        super().update(base_info, diff_data, request)

    def dayStart(self):
        super().dayStart()
        return None

    def talk(self):
        self.talk_turn += 1

        # 護衛記録の更新
        if self.talk_turn == 1:
            if 1 <= self.guarded_player <= 15:
                if self.ated_players_num == len(self.ated_players):
                    self.result_guard.add(self.guarded_player)
            self.guarded_player = 0
            self.ated_players_num = len(self.ated_players)

        return super().talk()

    def vote(self):
        return super().vote()

    def guard(self):
        #    printする場合は、print_onをTrueに変更
        print_on = False

        #    確定黒と確定白の確認
        #    確定白は自分目線確定白も含む
        true_black = self.alive.copy()
        true_white = self.alive.copy()
        for key in self.divineders - self.fake_divineders:
            true_black &= self.result_all_divineders[key]["black"]
            true_white &= self.result_all_divineders[key]["white"]
        true_white |= self.result_guard & self.alive
        if print_on:
            print("true_black:", true_black)
            print("true_white:", true_white)
            print("現段階のresult_guard:", result_guard)

        # (1)占いCOが3人以上いた場合、生きている霊能CO(0番目か1番目)がいれば霊能COを守る
        if len(self.divineders) >= 3:
            if set(self.COm[:1]) & self.alive:
                target = random.choice(list(set(self.COm[:1]) & self.alive))
                self.guarded_player = target
                if print_on: print("guard:占いCOが3人以上で霊媒が生きている場合:", target)
                return target

        #    使うかわからないので、コメントアウトした状態です
        #    mamoruをTrueにしたら動きます
        # (2)初日に黒出されが処刑された、かつ霊能COがひとりで、霊能が生きていたら霊能を守る
        #    日付の条件と黒出されが処刑されたかの条件以外は(2)と一緒
        mamoru = True
        if mamoru:
            if self.base_info["day"] == 1:
                divined_black = set()
                for key in self.divineders:
                    divined_black |= self.result_all_divineders[key]["black"]
                if self.exed_players[0] in divined_black:
                    if len(self.COm) == 1 and self.COm[0] in self.alive:
                        target = self.COm[0]
                        self.guarded_player = target
                        if print_on: print("guard:初日黒だされ処刑->霊能1人なら霊能守って結果の確認:", target)
                        return target

        # (3)真占いである可能性がある占い師の確認
        #    生きているdivinedersから、fake_divinedersとlikely_fake_divinedersを除いた集合に人がいたら、その人を守る
        if self.alive & self.divineders - self.fake_divineders - self.likely_fake_divineders:
            target = random.choice(list(self.alive & self.divineders - self.fake_divineders - self.likely_fake_divineders))
            self.guarded_player = target
            if print_on: print("guard:真っぽい占い師:", target)
            return target

        # (4)COmが1人であれば、その人を守る
        #    COmが2人以上いて片方死んでいる場合などは含まない
        if len(self.COm) == 1 and self.COm[0] in self.alive:
            target = self.COm[0]
            self.guarded_player = target
            if print_on: print("guard:COmが1人:", target)
            return target

        # (5)確定白がいたら、確定白を守る
        if true_white:
            target = random.choice(list(true_white))
            self.guarded_player = target
            if print_on: print("guard:確定白:", target)
            return target

        # (6)自分、確定黒、確定偽占い師、自分目線確定偽占い師を除いて、生きている人を守る
        if self.alive - {int(self.base_info['agentIdx'])} - true_black\
                - self.fake_divineders - self.likely_fake_divineders:
            target = random.choice(list(self.alive - {int(self.base_info['agentIdx'])}\
                    - true_black - self.fake_divineders - self.likely_fake_divineders))
            self.guarded_player = target
            if print_on: print("guard:確定黒、偽占い以外:", target)
            return target

        # (7)自分を除いて、生きている人を守る
        target = random.choice(list(self.alive - {int(self.base_info['agentIdx'])}))
        self.guarded_player = target
        if print_on: print("guard:生きていれば誰でも:", target)
        return target

    def finish(self):
        return None
