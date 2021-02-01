#!/usr/bin/env python
# coding: utf-8
# author: HALU Taichi Hosoi
# Medium 15 sub class
# ┏━┳━━┓
# ┃ ┃ ━┫
# ┃ ┣━┓┃
# ┗━┻━人村

import aiwolfpy.contentbuilder as cb  # aiwolfpyからプロトコルを生成する関数を流用

import HeVillager_15 as VillagerBehavior
import util
import random

class MediumBehavior(VillagerBehavior.VillagerBehavior):
    """
    霊媒師の振る舞い
    """

    def __init__(self, agent_name):
        super().__init__(agent_name)

    def initialize(self, base_info, diff_data, game_setting):
        super().initialize(base_info, diff_data, game_setting)
        self.result_medium = {'black': set(), 'white': set()}  # 霊媒結果の初期化
        self.result_medium_new = []  # 最新霊媒結果のリスト [エージェント番号, 0(人)or1(狼)]

    def update(self, base_info, diff_data, request):
        super().update(base_info, diff_data, request)

        # diff_dataからidentifyの結果を受け取って、result_mediumとresult_medium_newに格納する処理
        if request == "DAILY_INITIALIZE":
            for i in range(diff_data.shape[0]):
                if diff_data["type"][i] == "identify":
                    content = diff_data["text"][i].split()
                    if content[2] == 'HUMAN':
                        self.result_medium['white'].add(int(content[1][6:8]))
                        self.result_medium_new = [[int(content[1][6:8]), 0]]
                    else:
                        self.result_medium['black'].add(int(content[1][6:8]))
                        self.result_medium_new = [[int(content[1][6:8]), 1]]
                        # print(self.result_medium)

        # likely_fake_divineders (霊能) の更新
        # 自分の霊媒結果と矛盾した占い師と、自分に黒だしした占い師を、likely_fake_divinedersに入れる
        for CO_seer in list(self.divineders):
            if int(self.base_info['agentIdx']) in self.result_all_divineders[CO_seer]["black"]:
                self.likely_fake_divineders.add(CO_seer)
            if self.result_medium["black"] & self.result_all_divineders[CO_seer]["white"]:
                self.likely_fake_divineders.add(CO_seer)
            if self.result_all_divineders[CO_seer]["white"] & self.result_medium["black"]:
                self.likely_fake_divineders.add(CO_seer)


    def dayStart(self):
        super().dayStart()
        return None

    def talk(self):
        # printする場合は、print_onをTrueに変更
        print_on = False

        # talk_turnの更新
        self.talk_turn += 1

        # 1日目2ターン目に霊媒CO
        if self.base_info["day"] == 1 and self.talk_turn == 2:
            if print_on: print("SEER:COmedium")
            return cb.comingout(self.base_info['agentIdx'], "MEDIUM")

        # 最新霊媒結果があれば、発表
        elif self.result_medium_new:
            who, result = self.result_medium_new.pop(0)
            result = "WEREWOLF" if result else "HUMAN"
            if print_on:
                print("who:Agent" + str(who) + ", result:" + result)
                print("result_medium_new:", self.result_medium_new, "<-中身が空であればOK")
            return cb.identified(who, result)

        # 霊媒結果がなければ村人と同じ
        return super().talk()

    def vote(self):
        # vote_candに対し、他の人の投票表明が2番目に多かった人に投票
        # 1% の確率で村人と同じところに投票する (細井ノイズ)

        # vote_candで投票候補を選定し、candに入れる
        cands = self.vote_cand()

        # talk_vote_list の中から2番目に多く投票宣言された人をとってくる操作
        # max_frequent_2の第三引数を0にすると、2番目に多いエージェントを取得できる
        most_voted = util.max_frequent_2(self.talk_vote_list, cands, 0)
        judge_num = random.random()
        if judge_num >= 0.01:
            return most_voted
        else:
            return super().vote()

    def vote_cand(self):
        # printする場合は、print_onをTrueに変更
        print_on = False

        under_7 = False

        # (0)生き残り人数が7人以下になった場合の処理
        if under_7:
            if len(self.alive) <= 7 and self.under_7_vote:
                # 前日の霊媒結果が白の時
                if self.exed_players and self.exed_players[-1] in self.result_medium['white']:
                    # 初めて7人以下になった時の処理
                    if self.under_7_vote.pop(0, None):
                        # self.under_7_voteを、self.aliveに入ってる数をキーにして、それぞれに0を値とした辞書に変更
                        self.under_7_vote = {i: 0 for i in self.alive}
                    # 前日の処刑者に投票した人がいたら、辞書のその人の値を+1する
                    for i in set(j+1 for j in range(15) if self.yesterday_vote_list[j] == self.exed_players[-1]) & self.alive:
                        if i in self.under_7_vote:
                            self.under_7_vote[i] += 1
                    # 同じ日に複数回参照することがないように、self.yesterday_vote_listの中身を全て0にする
                    self.yesterday_vote_list = self.vote_list[:]
                    # 辞書のキーになっている人で、生きていない人がいたら削除
                    for i in set(self.under_7_vote.keys()) - self.alive:
                        self.under_7_vote.pop(i,None)
                    # 辞書が空でなければ、最多得票者に投票した回数が多い人の集合を返す
                    if len(self.under_7_vote):
                        if print_on: print("under_7_vote:", self.under_7_vote)
                        under_7_max_vote = {i[0] for i in self.under_7_vote.items()\
                                            if i[1] == max(self.under_7_vote.values())}
                        if print_on: print("under_7_max_vote:", under_7_max_vote)
                        return under_7_max_vote
                    if print_on: print("under_7_vote:", self.under_7_vote)

        # (1)霊能COが複数いた場合、自分以外の霊能CO者に投票
        if len(self.COm) >= 2:
            if set(self.COm) & self.alive - {int(self.base_info['agentIdx'])}:
                return set(self.COm) & self.alive - {int(self.base_info['agentIdx'])}

        #    確定黒と確定白の確認
        #    生きている人から，fake_divinederを除くdivinedersの占い黒結果の共通部分を確認
        true_black = self.alive.copy()
        true_white = self.alive.copy()
        for key in self.divineders - self.fake_divineders:
            true_black &= self.result_all_divineders[key]["black"]
            true_white &= self.result_all_divineders[key]["white"]
        if print_on: print("true_black:", true_black)

        # (2)確定黒がいたら確定黒に投票
        if self.divineders and true_black:
            return true_black

        fake_on = False

        # (3)確定偽占い師がいたら、そいつに投票
        if fake_on:
            if self.fake_divineders & self.alive:
                if print_on: print("self.fake_divineders:", self.fake_divineders)
                return self.fake_divineders & self.alive

        # (4)占い結果を行った人(divineders)が３人以上いた場合、
        #    占い師が1人でも生きていて、
        #    かつ、霊能結果で黒と出された占い師が"devinedersの人数-2"未満なら、占い師に投票
        #    意味：「占い師3人以上」=「人狼が占いCOしている」なので、人狼を吊れるまで、占い師に投票を続ける
        if len(self.divineders) >= 3:
            if self.divineders & self.alive:
                # 自分の霊媒結果で黒とでてない占い師が3人以上なら、
                # その中に人狼が(おそらく)混じっているはずなので、生きている占い師の中から投票
                if len(self.divineders - self.result_all_mediums[int(self.base_info["agentIdx"])]["black"]) >= 3:
                    if print_on: print("占い師3人以上で、その中に人狼がいると思われる場合")
                    return self.divineders & self.alive

        #    may_blackの確認
        #    信用できる占い師が出した黒結果の和集合からdivinedersを除いた集合
        may_black = set()
        for key in self.divineders - self.fake_divineders - self.likely_fake_divineders:
            may_black |= self.result_all_divineders[key]['black']
        may_black -= self.divineders
        if print_on: print("may_black:", may_black)

        # (5)may_blackが生きていれば投票
        if may_black & self.alive - {int(self.base_info["agentIdx"])}:
            return may_black & self.alive - {int(self.base_info["agentIdx"])}

        not_fake_divineders_greys = self.alive.copy()
        for key in self.divineders - self.fake_divineders - self.likely_fake_divineders:
            not_fake_divineders_greys -= self.result_all_divineders[key]["black"]
            not_fake_divineders_greys -= self.result_all_divineders[key]["white"]

        # (6)自分目線でグレーな人(占われていないかつ役職持ちではない人)に投票
        my_greys = not_fake_divineders_greys - self.divineders - self.COs - set(self.COm)\
                    - true_white - {int(self.base_info["agentIdx"])}
        if print_on: print("my_greys:", my_greys)
        if my_greys:
            return my_greys

        #    それもいなければ生きている人から選ぶ
        if print_on: print("自分以外の誰かに投票")
        return self.alive - {int(self.base_info["agentIdx"])}

    def finish(self):
        return None
