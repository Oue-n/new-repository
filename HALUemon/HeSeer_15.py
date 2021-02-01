#!/usr/bin/env python
# coding: utf-8
# author: HALU Taichi Hosoi
# Seer 15 sub class
# ┏━┳━━┓
# ┃ ┃ ━┫
# ┃ ┣━┓┃
# ┗━┻━人村

import aiwolfpy.contentbuilder as cb  # aiwolfpyからプロトコルを生成する関数を流用

import HeVillager_15 as VillagerBehavior
import random
import util


class SeerBehavior(VillagerBehavior.VillagerBehavior):
    """
    占い師の振る舞い
    """

    def __init__(self, agent_name):
        super().__init__(agent_name)

    def initialize(self, base_info, diff_data, game_setting):
        super().initialize(base_info, diff_data, game_setting)
        self.result_seer = {'black': set(), 'white': set()}  # 占い結果の初期化
        self.result_seer_new = []  # 最新占い結果のリスト [エージェント番号, 0(人)or1(狼)]
        # 最新結果のみ入れておく, talkで結果発表後に削除

    def update(self, base_info, diff_data, request):
        super().update(base_info, diff_data, request)

        # diff_dataからdivineの結果を受け取って、result_seerとresult_seer_newに格納する処理
        if request == "DAILY_INITIALIZE":
            for i in range(diff_data.shape[0]):
                if diff_data["type"][i] == "divine":
                    content = diff_data["text"][i].split()
                    if int(content[1][6:8]) in range(1, 16):
                        if content[2] == 'HUMAN':
                            self.result_seer['white'].add(int(content[1][6:8]))
                            self.result_seer_new = [[int(content[1][6:8]), 0]]
                        else:
                            self.result_seer['black'].add(int(content[1][6:8]))
                            self.result_seer_new = [[int(content[1][6:8]), 1]]
        # print(self.result_seer)

    def dayStart(self):
        super().dayStart()
        return None

    def talk(self):
        # printする場合は、print_onをTrueに変更
        print_on = False

        # talk_turnの更新
        self.talk_turn += 1
        if print_on: print("SEER:day=" + str(self.base_info["day"]) + ",turn=" + str(self.talk_turn))

        # 1日目1ターン目に占いCO
        if self.base_info["day"] == 1 and self.talk_turn == 1:
            if print_on: print("SEER:COseer")
            return cb.comingout(self.base_info['agentIdx'], "SEER")

        # 最新占い結果があれば、発表
        elif self.result_seer_new:
            who, result = self.result_seer_new.pop(0)
            result = "WEREWOLF" if result else "HUMAN"
            if print_on:
                print("who:Agent" + str(who) + ", result:" + result)
                print("result_seer_new:", self.result_seer_new, "<-中身が空であればOK")
            return cb.divined(who, result)

        # 占い結果がなければ村人と同じ
        return super().talk()

    def vote(self):
        # 細井ノイズ入り

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
        #    printする場合は、print_onをTrueに変更
        print_on = False
        if print_on:
            print("")
            print("seer_vote_cand")

        # (1)確定黒がいれば確定黒に投票
        #    確定偽占い師以外占い師の、黒結果の共通部分が生きていれば、それらの集合を返す
        true_black = self.alive.copy()
        for key in self.divineders - self.fake_divineders:
            true_black &= self.result_all_divineders[key]['black']
        if print_on: print("true_black:", true_black)
        if true_black:
            return true_black

        # (2)自分が黒だしした人が生きていたら、それらの集合を返す
        if self.result_seer['black'] & self.alive:
            if print_on: print("self.result_seer['black'] & self.alive:",self.result_seer['black'] & self.alive)
            return self.result_seer['black'] & self.alive

        # (3)確定偽占い師が生きていたら、それらの集合を返す
        if self.fake_divineders & self.alive:
            if print_on: print("self.fake_divineders & self.alive:", self.fake_divineders & self.alive)
            return self.fake_divineders & self.alive

        # (4)占い結果を行った人(divineders)が３人以上いた場合、
        #    自分以外の占い師が1人でも生きているなら、その人に投票
        if len(self.divineders) >= 3:
            if self.divineders & self.alive - {int(self.base_info["agentIdx"])}:
                return self.divineders & self.alive - {int(self.base_info["agentIdx"])}

        #    may_blackについて
        #    1,may_blackに自分と確定偽占い師以外の占い師の黒だしの和集合をとる
        #    2,その中から自分の占い結果と自分をのぞく
        may_black = set()
        for key in self.divineders - self.fake_divineders - {int(self.base_info["agentIdx"])}:
            may_black |= self.result_all_divineders[key]['black']
        may_black -= self.result_seer['white'] | self.result_seer['black'] | {int(self.base_info["agentIdx"])}
        if print_on: print("may_black:", may_black)

        #    my_greysについて
        #    自分がまだ占っていない、自分以外の生きているエージェントを入れる
        my_greys = self.alive - self.result_seer['white'] - self.result_seer['black'] - {int(self.base_info["agentIdx"])}
        if print_on: print("my_greys:", my_greys)

        # (5)確定偽占い師と自分以外の占い師が黒出していて、自分がまだその人を占っていなかった場合、(その集合をmay_blackと置く)
        #    1人または2人の霊媒師COが全員生きていたら、生きているmay_blackから投票する
        #    そうでなければ、自分がまだ占っていない人から、may_black,divineders,COm[:1]をのぞいた集合の中から投票する
        if may_black & self.alive:
            if set(self.COm) <= self.alive and len(self.COm) in [1, 2]:
                if print_on: print("may_black 1")
                return may_black & self.alive
            else:
                if print_on: print("may_black 2")
                return my_greys - may_black - self.divineders - set(self.COm[:1])

        # (6)上まででいなければ、divineders,COm[:1]を除いて自分がまだ占っていない人がいたら、そこに投票する
        if my_greys - self.divineders - set(self.COm[:1]):
            if print_on: print("my_greys 1")
            return my_greys - self.divineders - set(self.COm[:1])

        # (7)役職なしの自分のグレーがいなければ、COmよりdivinedersから先に投票する(自分以外)
        if self.divineders - {int(self.base_info["agentIdx"])}:
            if print_on: print("divineders 1")
            return self.divineders - {int(self.base_info["agentIdx"])}

        # (8)自分以外の生きているエージェントから投票する(エラー回避用)
        if print_on: print("alive 1")
        return self.alive - {int(self.base_info["agentIdx"])}

    def divine(self):
        # printする場合は、print_onをTrueに変更
        print_on = False

        # divine_candで占い候補を選定し、candに入れる
        cand = self.divine_cand()

        # candが空集合だった場合の対応
        if not cand:
            cand = self.alive - self.result_seer['white'] - self.result_seer['black'] \
                   - {int(self.base_info["agentIdx"])}
            print("divine_cand is not working!!")
        if print_on: print("cand:", cand)

        # 占い対象の決定
        next_divine = random.choice(list(cand))
        if print_on:
            print("next_divine:", next_divine)
            print("")

        return next_divine

    def divine_cand(self):
        #    printする場合は、print_onをTrueに変更
        print_on = False

        # (1)0日目の処理
        if not self.base_info['day']:
            if print_on:
                print("divine_cand start!!")
                print("agent_num:", self.base_info["agentIdx"])
                print("day:", self.base_info['day'])
            return self.alive - {int(self.base_info['agentIdx'])}

        # (2)全体でのグレー(生きていて占われていない人)からdivinedersをのぞく
        #    優先的に占いたい人の集合
        cand = self.greys - self.divineders - self.COs

        #    確認のためのprint文
        if print_on:
            print("")
            print("divine_cand start!!")
            print("agent_num:", self.base_info["agentIdx"])
            print("day:", self.base_info['day'])
            print("alive:", self.alive)
            print("greys:", self.greys)
            print("COm:", self.COm)
            print("COg:", self.COg)
            print("divineders:", self.divineders)
            print("vote_list:", self.vote_list)
            print("exed_players:", self.exed_players)
            print("fake_divineders:", self.fake_divineders)
            print("result_seer['white']:", self.result_seer['white'])
            print("result_seer['black']:", self.result_seer['black'])
            print("result_all_divineders:", self.result_all_divineders)

        # (3)もし霊能者COが1人しかいなければ、cand(占い候補)からは外す
        if len(self.COm) == 1:
            cand -= set(self.COm)

        # (4)霊能者COが複数でていた場合、その中に一人でも生き残っていたら、その中から優先される1人を選ぶ
        #    例えば、COm==[a,b,c,d,e]である時、b,c,d,e,aの順で先に該当した1人のみ、占い候補に入れられる
        if len(self.COm) >= 2 and len(set(self.COm) & cand) >= 1:
            if print_on: print("霊能CO複数のパターン")
            for i in self.COm[1:]:
                if i in cand:
                    return {i}
            return {self.COm[0]}

        # (5)狩人COが複数でていた場合、その中に一人でも生き残っていたら、その中から選ぶ
        if len(self.COg) >= 2 and len(self.COg & cand) >= 1:
            if print_on: print("狩人CO複数のパターン")
            return self.COg & cand

        #    may_blackについて
        #    1,may_blackに自分と確定偽占い師以外の占い師の黒だしの和集合をとる
        #    2,その中から自分の占い結果と自分をのぞく
        may_black = set()
        for key in self.divineders - self.fake_divineders - {int(self.base_info["agentIdx"])}:
            may_black |= self.result_all_divineders[key]['black']
        may_black -= self.result_seer['white'] | self.result_seer['black'] | {int(self.base_info["agentIdx"])}
        if print_on: print("may_black:", may_black)

        # (6)確定偽占い師と自分以外の占い師が黒出していて、自分がまだその人を占っていなかった場合、
        #    その人が生きていたら、その人を占う
        if may_black & self.alive:
            if print_on: print("他の占い師が黒だしした人がいたパターン")
            return may_black & self.alive

        #    vote_meについて
        #    投票した先に自分のエージェント番号があれば、投票元をvote_meに入れる
        vote_me = set()
        for i in range(15):
            if self.vote_list[i] == int(self.base_info["agentIdx"]):
                vote_me.add(i + 1)

        # (7)自分に投票しており、かつ全体のグレーであるエージェントがいれば、その中から選ぶ
        if len(vote_me & cand) >= 1:
            if print_on: print("自分に投票した全体グレーがいたパターン")
            return vote_me & cand

        #    vote_maxについて
        #    投票した先に前日処刑されたエージェント番号があれば、投票元をvote_maxに入れる
        vote_max = set()
        for i in range(15):
            if self.vote_list[i] == self.exed_players[-1]:
                vote_max.add(i + 1)

        # (8)3日目までは、全体のグレーであり、かつ前日の処刑者に投票したエージェントがいたら、その中から選ぶ
        #    4日目以降は、全体のグレーであり、かつ前日の処刑者に投票していないエージェントがいたら、その中から選ぶ
        if self.base_info['day'] <= 3:
            if len(vote_max & cand):
                if print_on: print("3日目までで前日処刑された人に投票した全体グレーがいたパターン")
                return vote_max & cand
        else:
            if len(cand - vote_max):
                if print_on: print("4日目以降で前日処刑された人に投票していない全体グレーがいたパターン")
                return cand - vote_max

        # (8)の内側のif文に入れなければ、ここまで到達する

        # (9)candから返す
        if cand:
            if print_on: print("candをそのまま")
            return cand

        # (10)占い師(自分以外)と霊媒師(1人)なら占い師を先に占う
        if (self.divineders | self.COs) & self.alive - {int(self.base_info["agentIdx"])}:
            if print_on: print("生きてるdivinedersとCOs")
            return (self.divineders | self.COs) & self.alive - {int(self.base_info["agentIdx"])}
        if set(self.COm) & self.alive:
            if print_on: print("生きてるCOm")
            return set(self.COm) & self.alive

        # (11)自分以外の生きているエージェントから占う(エラー回避用)
        if print_on: print("生きてるエージェント")
        return self.alive - {int(self.base_info['agentIdx'])}

    def finish(self):
        return None