#!/usr/bin/env python
# coding: utf-8
# author: HALU Taichi Hosoi
# Werewolf 15 sub class
# ┏━┳━━┓
# ┃ ┃ ━┫
# ┃ ┣━┓┃
# ┗━┻━人村

# general packages
import random
import collections

# basic for aiwolf package
import aiwolfpy.contentbuilder as cb  # aiwolfpyからプロトコルを生成する関数を流用
import util
import parse_content

# derivation from 5 mura packages
# import recognizer
import textgenerator

# derivation from super class
import HeVillager_15 as VillagerBehavior

class WerewolfBehavior(VillagerBehavior.VillagerBehavior):

    def __init__(self, agent_name):
        super().__init__(agent_name)

    def initialize(self, base_info, diff_data, game_setting):
        super().initialize(base_info, diff_data, game_setting)
        self.result_Wmed = []  # 偽霊媒結果の初期化
        self.whisper_turn = 0
        self.pp_mode = 1
        self.stealth = 0
        self.first_identify = 0

        self.shonichi_target = 0
        self.kurodashi = set()
        self.shirodashi = set()

        self.most_voted = 0

        self.SPcounter = 0

        # 狼仲間の取得
        self.wolfs = set(map(lambda i: int(i), self.base_info["roleMap"].keys()))
        # print("self.wolfs", self.wolfs)

        # 振舞い方の決定
        judger = random.random()
        if judger <= 0.2:
            # 占い師の動き方(0~20)
            self.role_decision = 0
        elif judger > 0.2 and judger <= 0.5:
            # ステルスの動き方(20~50)
            self.role_decision = 1
        else:
            # 霊媒師の動き方(50~100)
            self.role_decision = 2

    def update(self, base_info, diff_data, request):
        super().update(base_info, diff_data, request)

        # 襲撃結果の受け取り
        # if request == "DAILY_INITIALIZE":
        #     for i in range(diff_data.shape[0]):
        #         if diff_data["type"][i] == "attack":
        #             # print(diff_data["text"][i])
        #             if "false" in diff_data["text"][i]:
        #                 self.attack_success = False
        #             else:
        #                 self.attack_success = True
        # print(self.result_Wmed)

        # likely_fake_divineders (人狼) の更新
        for CO_seer in self.divineders:
            if self.wolfs & self.result_all_divineders[CO_seer]["white"]:
                self.likely_fake_divineders.add(CO_seer)
            if self.result_all_divineders[CO_seer]["black"] - self.wolfs:
                self.likely_fake_divineders.add(CO_seer)

    def dayStart(self):
        super().dayStart()
        self.whisper_turn = 0
        return None

    def talk(self):
        self.talk_turn += 1
        self.attack_judge = 0
        # 占い師talk
        if self.role_decision == 0:
            # 初日　
            #     1ターン目　占いCO　
            #     2ターン目　全体から占いと霊能と人狼を引いた集合からランダムに黒出し　
            #     3ターン目以降　その人に投票宣言(voteもこの黒出しに合わせる)
            # 1 ターン目に "MEDIUM" を宣言する
            if self.base_info["day"] == 1:
                if self.stealth == 0:
                    if self.talk_turn == 1:
                        CO_SEER = cb.comingout(self.base_info['agentIdx'], "SEER")
                        return CO_SEER
                    elif self.talk_turn == 2:
                        if self.COs - {int(self.base_info["agentIdx"])}:
                            self.shonichi_target = random.choice(list(self.COs - {int(self.base_info["agentIdx"])}))
                            self.kurodashi.add(self.shonichi_target)
                            return cb.divined(self.shonichi_target, "WEREWOLF")
                        else:
                            self.shonichi_target = random.choice(list(self.alive - self.COs - set(self.COm) - self.divineders))
                            self.kurodashi.add(self.shonichi_target)
                            return cb.divined(self.shonichi_target, "WEREWOLF")
                    elif self.talk_turn >= 3:
                        return cb.vote(self.shonichi_target)
                else:
                    return super().talk()

            # 二日目以降
            #     1ターン目　aliveから占いと霊能と人狼を引いた集合-占い済からrandomに白だし　
            #     2ターン目以降現状の投票候補から白だしを引いてvoteに渡し、それを発言
            #     1～２回だけ 1ターン目　alive人狼の集合からrandomに白だし　これは二日目以降30%程度の確率でやりたい
            #   7人以下になった時の特殊戦略
            #       狂人COの投票先が人狼以外ならそれに乗っかる
            #       人狼以外の最多得票者に投票　
            else:
                if self.stealth == 0:
                    judger = random.random()
                    if judger <= 0.7 and self.SPcounter <= 2:
                        if self.talk_turn == 1:
                            if self.alive - self.COs - set(self.COm) - self.divineders - self.kurodashi - self.shirodashi:
                                target = random.choice(list(self.alive - self.COs - set(self.COm) - self.divineders - self.kurodashi - self.shirodashi))
                                self.shirodashi.add(target)
                                return cb.divined(target, "HUMAN")
                            elif self.alive - self.kurodashi - self.shirodashi:
                                target = random.choice(list(self.alive - self.kurodashi - self.shirodashi))
                                self.shirodashi.add(target)
                                return cb.divined(target, "HUMAN")
                            elif self.alive & self.shirodashi:
                                target = random.choice(list(self.alive & self.shirodashi))
                                self.shirodashi.add(target)
                                return cb.divined(target, "HUMAN")
                            else:
                                target = random.choice(list(self.alive & self.kurodashi))
                                self.kurodashi.add(target)
                                return cb.divined(target, "WEREWOLF")
                        else:
                            target = self.vote()
                            return cb.vote(target)
                    else:
                        self.SPcounter += 1
                        if self.talk_turn == 1:
                            if self.alive & self.wolfs - {int(self.base_info["agentIdx"])}:
                                target = random.choice(list(self.alive & self.wolfs - {int(self.base_info["agentIdx"])}))
                                self.shirodashi.add(target)
                                return cb.divined(target, "HUMAN")
                            else:
                                target = self.vote()
                                self.shirodashi.add(target)
                                return cb.divined(target, "HUMAN")
                        else:
                            target = self.vote()
                            return cb.vote(target)
                else:
                    return super().talk()
            return super().talk()

        # stealth talk
        if self.role_decision == 1:
            return super().talk()

        # 霊媒師 talk
        if self.role_decision == 2:
            # 1 ターン目に "MEDIUM" を宣言する
            if self.base_info["day"] == 1:
                if self.talk_turn == 1:
                    if self.stealth == 0:
                        CO_MEDIUM = cb.comingout(self.base_info['agentIdx'], "MEDIUM")
                        return CO_MEDIUM
                    else:
                        # CO_VILLAGER = cb.comingout(self.base_info['agentIdx'], "VILLAGER")
                        # return CO_VILLAGER
                        return super().talk()

                # 他は村人と同じ会話をする
                else:
                    return super().talk()

            # 二日目以降の人狼の挙動
            else:
                # 偽霊能者の動き方をする時
                if self.stealth == 0:
                    if self.talk_turn == 1:
                        # 処刑された人物が COm の中にいた場合
                        # (ここに入るということは自分以外の人狼が COm はありえないということ)
                        if self.exed_players[-1] in set(self.COm):
                            # COm の 1 人目の占いをする場合
                            if self.first_identify == 0:
                                # 自分以外の COm がいた場合の話
                                if len(self.COm) >= 2:
                                    # 1人目のみ自分以外の霊能CO者が釣られたらそいつのことを黒という
                                    IDENTIFIED_BLACK = cb.identified(self.exed_players[-1], "WEREWOLF")
                                    self.first_identify = 1
                                    return IDENTIFIED_BLACK
                                # 他は村人と同じ会話をする
                                else:
                                    return super().talk()

                            # COm の 2 人目以降の占いをする場合，以降の Medium 宣言者は全て白を出す
                            if self.first_identify == 1:
                                if len(self.COm) >= 2:
                                    # そいつが先に釣られた場合はそいつを黒と言う
                                    IDENTIFIED_WHITE = cb.identified(self.exed_players[-1], "HUMAN")
                                    self.first_identify = 1
                                    return IDENTIFIED_WHITE
                                # 他は村人と同じ会話をする
                                else:
                                    return super().talk()

                        # 処刑された人物が COm の中にいない場合，正直に identify する．ただし例外あり．
                        else:
                            # これが例外．偽の黒出しをされた人が処刑された場合．
                            black_cand = set()
                            for i in self.divineders:
                                black_cand |= self.result_all_divineders[i]['black']
                            black_cand -= self.wolfs
                            if self.exed_players[-1] in black_cand:
                                IDENTIFIED_BLACK = cb.identified(self.exed_players[-1], "WEREWOLF")
                                return IDENTIFIED_BLACK
                            else:
                                # 死んだ人が人狼であった場合，正直に黒出しをする
                                if self.exed_players[-1] in set(self.wolfs):
                                    IDENTIFIED_BLACK = cb.identified(self.exed_players[-1], "WEREWOLF")
                                    return IDENTIFIED_BLACK
                                else:
                                    IDENTIFIED_WHITE = cb.identified(self.exed_players[-1], "HUMAN")
                                    return IDENTIFIED_WHITE
                    if self.talk_turn >= 2:
                        return super().talk()
                # 偽村人の動き方をする時
                else:
                    return super().talk()


    def vote(self):
        if self.base_info["day"] == 1:
            if self.stealth == 0:
                if self.role_decision == 0:
                    return self.shonichi_target
                else:
                    cands = self.decide_vote_cand()
                    most_voted = util.max_frequent_2(self.talk_vote_list, cands, 1)
                    return most_voted
            else:
                cands = self.decide_vote_cand()
                most_voted = util.max_frequent_2(self.talk_vote_list, cands, 1)
                return most_voted
        else:
            # 特殊処理：生存者数が 7 人以下になった場合
            if len(self.alive) <= 7:
                # 狂人 CO をしている人がいれば
                if len(self.COp) != 0:
                    possessed_vote = []
                    # その人の投票先を取得して
                    for i in self.COp:
                        possessed_vote.append(self.talk_vote_list[int(i)-1])
                    # 人狼へ向いている投票を除いた上で
                    for W in list(self.wolfs):
                        possessed_vote = [i for i in possessed_vote if i != W]
                    if len(possessed_vote) != 0:
                        cands = max_frequent(possessed_vote)
                        target = random.choice(list(cands))
                        return target
                    else:
                        cands = self.alive - self.wolfs
                        target = random.choice(list(cands))
                        return target
                else:
                    if self.decide_vote_cand() - self.shirodashi:
                        # vote_candに対し、他の人の投票表明が一番多かった人に投票
                        # 投票する候補を叩き出してるだけ
                        cands = self.decide_vote_cand() - self.shirodashi
                        # talk_vote_list の中から最大の人をとってくる操作
                        most_voted = util.max_frequent_2(self.talk_vote_list, cands, 1)
                        return most_voted
                    else:
                        cands = self.decide_vote_cand()
                        # talk_vote_list の中から最大の人をとってくる操作
                        most_voted = util.max_frequent_2(self.talk_vote_list, cands, 1)
                        return most_voted
            else:
                if self.decide_vote_cand() - self.shirodashi:
                    # vote_candに対し、他の人の投票表明が一番多かった人に投票
                    # 投票する候補を叩き出してるだけ
                    cands = self.decide_vote_cand() - self.shirodashi
                    #talk_vote_list の中から最大の人をとってくる操作
                    most_voted = util.max_frequent_2(self.talk_vote_list, cands, 1)
                    return most_voted
                else:
                    cands = self.decide_vote_cand()
                    # talk_vote_list の中から最大の人をとってくる操作
                    most_voted = util.max_frequent_2(self.talk_vote_list, cands, 1)
                    return most_voted

    def whisper(self):
        self.whisper_turn += 1
        """
        一番最初に霊能COをすることを伝える
        attack_voteで襲撃の投票をする先を宣言する
        """

        if self.role_decision == 0:
        # 0 日目 1 ターン目に "SEER" を宣言する
            if self.base_info["day"] == 0:
                if self.whisper_turn == 1:
                    return cb.comingout(self.base_info['agentIdx'], 'SEER')
                if self.whisper_turn == 2:
                    #1 ターン目に whisper の中で仲間の人狼が SEER CO をしていた場合
                    if len(self.W_COs) >= 2 or len(self.W_COm) >= 1:
                        self.stealth = 1
                        return cb.comingout(self.base_info['agentIdx'], 'VILLAGER')
                    else:
                        return cb.skip()
                if self.whisper_turn >= 3:
                    return cb.skip()
                #return cb.over()
                return cb.skip()

        if self.role_decision == 1:
        # 0 日目 1 ターン目に ステルス挙動 を宣言する
            if self.base_info["day"] == 0:
                if self.whisper_turn == 1:
                    return cb.comingout(self.base_info['agentIdx'], 'VILLAGER')
                if self.whisper_turn >= 2:
                    return cb.skip()
                #return cb.over()
                return cb.skip()

        if self.role_decision == 2:
        # 0 日目 1 ターン目に "MEDIUM" を宣言する
            if self.base_info["day"] == 0:
                if self.whisper_turn == 1:
                    return cb.comingout(self.base_info['agentIdx'], 'MEDIUM')
                if self.whisper_turn == 2:
                    #1 ターン目に whisper の中で仲間の人狼が MEDIUM CO をしていた場合
                    if len(self.W_COm) >= 2 or len(self.W_COs) >= 1:
                        self.stealth = 1
                        return cb.comingout(self.base_info['agentIdx'], 'VILLAGER')
                if self.whisper_turn >= 3:
                    return cb.skip()
                #return cb.over()
                return cb.skip()

        # 1 日目以降， 1 ターン目に "ATTACK" する対象を宣言する
        if self.base_info["day"] >= 1:
            if self.whisper_turn == 1:
                return cb.attack(self.attack())
            else:
                #return cb.over()
                return cb.skip()

        #return cb.over()
        return cb.skip()

    def attack(self):
        # 占い師挙動を取るときのattack
        if self.role_decision == 0:
            # 初日霊能を襲撃，いなければグレーから襲撃
            if self.base_info["day"] == 1:
                cand_1 = self.COm
                if (len(cand_1) != 0):
                    # print(COSATC1)
                    return random.choice(list(cand_1))
                else:
                    # 初日グレーとは　生存者から，人狼と占い師(結果まで言ってる人)と霊能者を引いたもの
                    # cand_2 = self.alive - self.wolfs - self.divineders - set(self.COm)
                    cand_2 = self.greys
                    # print(COSATC2)
                    return random.choice(list(cand_2))

            # 二日目以降グレーとは　生存者から，人狼と占い師(結果まで言ってる人)と霊能者を引いたもの．
            if self.base_info["day"] >= 2:
                cand_3 = self.greys
                if (len(cand_3) != 0):
                    # print(COSATC3)
                    return random.choice(list(cand_3))
                else:
                    return random.choice(list(self.alive - self.wolfs))

            # エラー回避
            return random.choice(list(self.alive - self.wolfs))

        # ステルス挙動を取るときのattack
        if self.role_decision == 1:
            if self.base_info["day"] == 1:
                likely_true_divineders = self.alive & self.divineders - self.fake_divineders\
                                         - self.wolfs - self.likely_fake_divineders
                # 初日は真占いがわかれば真占いを襲撃
                if len(likely_true_divineders) == 1:
                    # print(COSATC1)
                    return list(likely_true_divineders)[0]
                # わからなければ占い師からrandomに襲撃
                elif len(self.divineders & self.alive - self.wolfs) != 0:
                    cand_1 = self.divineders & self.alive - self.wolfs
                    return random.choice(list(cand_1))
                # それもいなければ生きている人からランダム
                else:
                    cand_2 = self.alive - self.wolfs
                    # print(COSATC2)
                    return random.choice(list(cand_2))

            # 二日目以降　霊能が生きていたら襲撃
            # self.attack_judgeで0なら襲撃失敗，1なら襲撃成功
            if self.base_info["day"] >= 2:
                AJ_set = set()
                AJ_set.add(self.attack_judge)
                if 0 in AJ_set:
                    #print("COSATC0")
                    # 霊能者を噛み殺す
                    if set(self.COm) - self.wolfs:
                        cand_3 = set(self.COm) - self.wolfs
                        # print("COSATC3")
                        return random.choice(list(cand_3))
                    elif self.greys - self.wolfs:
                        cand_4 = self.greys - self.wolfs
                        # print("COSATC4")
                        return random.choice(list(cand_4))
                    else:
                        cand_5 = self.alive - self.wolfs
                        # print("COSATC5")
                        return random.choice(list(cand_5))
                else:
                    cand_6 = self.greys - self.wolfs
                    #print("COSATC6")
                    return random.choice(list(cand_6))


            # エラー回避
            return random.choice(list(self.alive - self.wolfs))

        #  _  _        _  _  ____  ____  __  _  _  _  _
        # / )( \      ( \/ )(  __)(    \(  )/ )( \( \/ )
        # \ /\ / ____ / \/ \ ) _)  ) D ( )( ) \/ (/ \/ \
        # (_/\_)(____)\_)(_/(____)(____/(__)\____/\_)(_/
        # 霊能挙動を取るときのattack
        if self.role_decision == 2:
            # ①likely_true_seerがいたら噛む
            likely_true_seers = (self.divineders & self.alive) - self.fake_divineders - self.likely_fake_divineders
            if (likely_true_seers):
                # print(1)
                return random.choice(list(likely_true_seers))

            # ②divinedersが2人以上いて全員生きていたらその中から噛む
            # print(1.5)
            if (len(self.divineders) >= 2) and (self.divineders & self.alive) == self.divineders:
                # print(2)
                return random.choice(list(self.divineders))

            # print(2.5)
            nonW_COg = self.COg & self.alive - self.wolfs
            # ③(狩人 CO している人がいれば) 狩人CO - wolfを噛む
            if (len(list(nonW_COg)) >= 1):
                # print(3)
                return random.choice(list(nonW_COg))

            # print(3.5)
            # ④result_all_divineders - fake_seers - likely_fake_seers の出した白の中から噛む(COmとCOsを除いて)
            # 白出しされているエージェントの候補集合
            white_cand = set()
            # 少なくとも偽物だとは思えないそれっぽい占い師の集合
            may_seer = self.divineders - self.fake_divineders - self.likely_fake_divineders
            # それっぽい占い師の集合をキーに持つ白出しされたエージェント
            for i in may_seer:
                white_cand = white_cand | self.result_all_divineders[i]['white']  # <- ちょっと危険な匂いがする...
            white_cand = white_cand - set(self.COm)
            white_cand = white_cand - self.COs
            if (white_cand & self.alive):
                # print(4)
                return random.choice(list(white_cand))

            # print(4.5)
            # ⑤alive - COs - COm - wolfから噛む
            cand_5 = self.alive - self.COs - set(self.COm) - self.wolfs
            if (len(cand_5) != 0):
                # print(5)
                return random.choice(list(cand_5))

            # print(5.5)
            # ⑥alive - COs - wolfから噛む
            cand_6 = self.alive - self.COs - self.wolfs
            if (len(cand_6) != 0):
                # print(6)
                return random.choice(list(cand_6))

            # print(6.5)
            # ⑦alive - wolfから噛む
            cand_7 = self.alive - self.wolfs
            if (len(cand_7) != 0):
                # print(7)
                return random.choice(list(cand_7))

            # print(8)
            return random.choice(list(self.alive - self.wolfs))

    def finish(self):
        return None

    # pp モードかどうかを判定する関数
    def pp_judger(self):
        # A or B
        # A: 生き残っている POSSESSED or SEER の占い師ぶってる人の数が 2 以上である
        # B: 自身が人狼として、狂人であるとわかっている人の数が 1 以上である
        if len(self.divineders & self.alive - self.wolfs) >= 2 or \
                len(set(self.likely_fake_divineders.keys()) & set(self.alive)) - len(set(self.wolfs)) >= 1:
            if (len(self.alive) == len(set(self.wolfs) & set(self.alive)) * 2 + 1):
                print("ppmode ON")
                self.pp_mode = 1
                print("A_True & B_True pattern")
                #   真占い師と狂人が生きており、狂人が生きている場合
                #       真占い師がわかるので、真占い師に投票する

        #     else:
        #         print("ppmode ON")
        #         self.pp_mode = 1
        #         print("A_True & B_False pattern")
        #         #   真占い師と狂人が生きているが、どちらかわからない場合
        #         #       ① 真占い師と狂人以外の人がいる状態: その候補のどれかに投票
        #         #       ② 真占い師と狂人以外の人がいない状態: random 投票 (占、狂、狼 の場合)
        #
        # else:
        #     if (len(self.alive) == len(set(self.wolfs) & set(self.alive)) * 2 + 1):
        #         print("ppmode ON")
        #         self.pp_mode = 1
        #         print("A_False & B_True pattern")
        #         #   真占い師が死んでいて、狂人が生きている場合
        #         #       狂人以外に投票する
        #     else:
        #         print("ppmode OFF")
        #         print("A_False & B_False pattern")
        #         print("UNCHI!!!!!!!!!!!!!!!!!!!!")
        #         print("IGUNORE!!!!!!!!!!!!!!!!!!")
        #         #   複雑な状態だからもう知らない〜〜

    def decide_vote_cand(self):
        """
        vote_cand
        """
        # 霊能COが複数いた場合
        if len(self.COm) >= 2:
            if set(self.COm) & self.alive - {int(self.base_info['agentIdx'])}:
                return set(self.COm) & self.alive - {int(self.base_info['agentIdx'])}
        # 確定黒 - wolfがいたらそれに投票
        true_black = self.alive.copy()
        for key in self.divineders - self.fake_divineders:
            true_black &= self.result_all_divineders[key]['black']
        if self.divineders and true_black - self.wolfs:
            return true_black - self.wolfs

        # 偽占い以外の黒だされ - wolfがいたら、そいつに投票
        may_black = set()
        for key in self.divineders - self.fake_divineders:
            may_black |= self.result_all_divineders[key]['black']
        if self.alive & may_black - self.wolfs:
            return self.alive & may_black - self.wolfs

        if self.greys - self.COg - set(self.COm) - self.COs - self.wolfs:
            return self.greys - self.COg - set(self.COm) - self.COs - self.wolfs
        """
        # 黒だされがいなければ、グレーのCOなし - wolfに投票
        if(len(may_black) == 0):
            #print("dv3")
            target = self.greys - self.COg - set(self.COm) - self.COs - self.wolfs
            return target
        """
        # 自分以外の誰か - wolfに投票 << 様子を見ながら修正していく >>
        return self.alive - {int(self.base_info['agentIdx'])} - self.wolfs

# 投票 index リストにおいて最も最頻の投票先を出力する関数
def max_frequent(l):
    # print("l:",l)
    # type="talk" において VOTE の宣言がない場合，そのように返す
    if all(x == 0 for x in l) == True:
        return set()
    # type="talk" において VOTE の宣言がある場合，最多票数のエージェント番号を返す
    else:
        # 0 獲得票数 0 のデータを削除する
        if 0 in l:
            l = [s for s in l if s != 0]
        max_cand = set()  # 最多票獲得エージェントを格納する set を用意
        sorted_res = collections.Counter(l).most_common()
        max_vallot = sorted_res[0][1]  # 最多獲得票数
        max_cand.add(sorted_res[0][0])  # 最多票獲得エージェントの 1 つめを格納

        # 2 つめ以降は，もし最大票数を獲得しているエージェントがあれば追加，そうでなければ探索終了
        for i in range(1, len(sorted_res)):
            if (sorted_res[i][1] == max_vallot):
                max_cand.add(sorted_res[i][0])
            else:
                break

        # choose_agent = random.sample(max_cand, 1)
        # print("max_cand:",max_cand)
        return max_cand