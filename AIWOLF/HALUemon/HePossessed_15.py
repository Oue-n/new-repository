# coding: utf-8
# author: HALU Taichi Hosoi
# Possessed 15 sub class
# ┏━┳━━┓
# ┃ ┃ ━┫
# ┃ ┣━┓┃
# ┗━┻━人村

import random
import collections

import aiwolfpy.contentbuilder as cb  # aiwolfpyからプロトコルを生成する関数を流用
import util

import HeVillager_15 as VillagerBehavior

class PossessedBehavior(VillagerBehavior.VillagerBehavior):

    def __init__(self, agent_name):
        super().__init__(agent_name)

    def initialize(self, base_info, diff_data, game_setting):
        self.kurodashi = set()
        self.ts_kurodashi = []
        self.shirodashi = set()
        self.result_seer = {"white":set(), "black":set()}

        self.SP = 0
        self.SP_target = 0

        super().initialize(base_info, diff_data, game_setting)

    def update(self, base_info, diff_data, request):
        super().update(base_info, diff_data, request)

    def dayStart(self):
        super().dayStart()
        self.talk_turn = 0
        return None

    def talk(self):
        """
        （案）Voteを呼び出して、talk_vote_listの中から、最多得票者に投票すると発言（便乗）
        """
        self.talk_turn += 1

        # 1 日目の 1 ターン目に "SEER" を宣言する
        if self.base_info["day"] == 1:
            if self.talk_turn == 1:
                CO_SEER = cb.comingout(self.base_info['agentIdx'], "SEER")
                return CO_SEER

            # 1 日目 2 ターン目、生きている中で、占いCO霊媒COを除いた集合の中から黒だし（COの数は問わない）
            if self.talk_turn == 2:
                # 占いCO3人の時、初日占いに黒出しする
                if len(self.COs) == 3:
                    vote_cand = self.COs - {int(self.base_info["agentIdx"])}
                    target = random.choice(list(vote_cand))
                    self.ts_kurodashi.append(target)
                    self.kurodashi.add(target)
                    fake_divine_res = cb.divined(target, "WEREWOLF")
                    return fake_divine_res
                else:
                    vote_cand = self.alive - self.COs - set(self.COm) - self.divineders
                    target = random.choice(list(vote_cand))
                    self.ts_kurodashi.append(target)
                    self.kurodashi.add(target)
                    fake_divine_res = cb.divined(target, "WEREWOLF")
                    return fake_divine_res

            # どこに投票するとか宣言しなくていいの？
            else:
                return super().talk()

        # # 2 日目以降の 1 ターン目に divine_cand からもらってきた集合の中からランダムにえらび、50 % で黒だし
        # if self.base_info["day"] >= 2:
        #     if self.talk_turn == 1:
        #         random_num = random.random()
        #         target = random.choice(list(self.decide_divine_cand()))
        #         if(random_num >= 0.5):
        #             self.shirodashi.add(target)
        #             self.result_seer["white"] = self.shirodashi
        #             #print(self.result_seer)
        #             fake_divine_res = cb.divined(target, "HUMAN")
        #             return fake_divine_res
        #         else:
        #             self.kurodashi.add(target)
        #             self.result_seer["black"] = self.kurodashi
        #             #print(self.result_seer)
        #             fake_divine_res = cb.divined(target, "WEREWOLF")
        #             return fake_divine_res
        #
        #     # どこに投票するとか宣言しなくていいの？
        #     else:
        #         return super().talk()

        """
        狂人の更新案(旧)
        (完) 黒出しが処刑されたら新たに黒出しをする
        占い師の白だしに黒を出す (decide_vote_cand に実装する)
        占い対象がグレーかすでに真占いが占っているかの判断は確率でもよい
        
        狂人の更新案(新)
        初日　ランダムに黒出し
        処刑されなかった場合　前日の得票数の多いところに白だしモードに入る
        処刑された場合　黒出しモードに入る　黒出し先は以下に従う
            占い師の白だしを所得して黒を出す
            占い師の白だしがいなければ前日に自分の黒出しに投票したひと-COしたひとを返す
            
        なお，7人以下になった時に特殊戦略を実行
            → 狂人COして真占いの白だしに投票
        """
        # 2 日目以降の 1 ターン目に divine_cand からもらってきた集合の中からランダムにえらび、50 % で黒だし
        if self.base_info["day"] >= 2:
            if len(self.alive) > 7:
                if self.talk_turn == 1:
                    # 黒出しした人が処刑された場合 -> 黒出しモード
                    if self.ts_kurodashi[-1] not in self.alive:
                        result_all_white = set()
                        non_me_divineders = self.divineders - {int(self.base_info["agentIdx"])}
                        for i in non_me_divineders:
                            result_all_white |= self.result_all_divineders[i]['white']
                        result_all_white &= self.alive
                        result_all_white -= set(self.COm)
                        result_all_white -= {int(self.base_info["agentIdx"])}
                        # 占い師の白出しが存在している場合
                        if result_all_white:
                            target = random.choice(list(result_all_white))
                            self.ts_kurodashi.append(target)
                            self.kurodashi.add(target)
                            self.result_seer["black"] = self.kurodashi
                            #print(self.result_seer)
                            fake_divine_res = cb.divined(target, "WEREWOLF")
                            return fake_divine_res
                        # 占い師の白出しが存在していない場合
                        else:
                            # 前日の自分の黒出しに投票した人の集合を取り出す
                            stupid = YMBV(self.vote_list, self.ts_kurodashi[-1])
                            # 前日の自分の黒出しに投票した人 - CO のなかからランダムに選んで黒出し
                            if stupid - self.COs - set(self.COm) - self.divineders - {self.ated_players[-1]}:
                                target = random.choice(list(stupid - self.COs - set(self.COm) - self.divineders - {self.ated_players[-1]}))
                            elif self.alive - self.COs - set(self.COm) - self.divineders - {self.ated_players[-1]}:
                                target = random.choice(list(self.alive - self.COs - set(self.COm) - self.divineders - {self.ated_players[-1]}))
                            else:
                                target = random.choice(list(self.alive - {int(self.base_info["agentIdx"])}))
                            self.kurodashi.add(target)
                            self.ts_kurodashi.append(target)
                            fake_divine_res = cb.divined(target, "WEREWOLF")
                            return fake_divine_res

                    # 黒出しした人が処刑されていない場合 -> 白出しモード
                    else:
                        # 前日の得票数が多いところに白出ししたい
                        noMAX_vote_list = [s for s in self.vote_list if s != self.exed_players[-1]]
                        noME_noMAX_vote_list = [s for s in noMAX_vote_list if s != int(self.base_info["agentIdx"])]
                        cand = max_frequent(noME_noMAX_vote_list)
                        if cand:
                            target = random.choice(list(cand))
                        #万が一投票が全く無ければランダムに投票しよう(最終手段のエラー回避)
                        else:
                            target = random.choice(list(self.alive - {int(self.base_info["agentIdx"])}))
                        self.shirodashi.add(target)
                        self.result_seer["white"] = self.shirodashi
                        # print(self.result_seer)
                        fake_divine_res = cb.divined(target, "HUMAN")
                        return fake_divine_res

                # どこに投票するとか宣言しなくていいの？
                else:
                    return super().talk()

            # 特殊戦略
            else:
                self.SP = 1
                # 狂人 CO をして
                if self.talk_turn == 1:
                    CO_POSSESSED = cb.comingout(self.base_info['agentIdx'], "POSSESSED")
                    return CO_POSSESSED
                # 真占い師の出した白出し先に投票
                if self.talk_turn >= 2:
                    likely_true_divineders = self.divineders - self.fake_divineders - {int(self.base_info["agentIdx"])}
                    if likely_true_divineders:
                        sac = set()
                        for i in likely_true_divineders:
                            sac &= self.result_all_divineders[i]['white']
                        if sac:
                            target = random.choice(list(sac))
                            self.SP_target = target
                            return cb.vote(target)
                        else:
                            cands = self.alive - {int(self.base_info["agentIdx"])}
                            target = util.max_frequent_2(self.talk_vote_list, cands, 1)
                            self.SP_target = target
                            return cb.vote(target)
                    else:
                        cands = self.alive - {int(self.base_info["agentIdx"])}
                        target = util.max_frequent_2(self.talk_vote_list, cands, 1)
                        self.SP_target = target
                        return cb.vote(target)

        return super().talk()

    def vote(self):
        if self.SP == 0:
            # vote_candに対し、他の人の投票表明が一番多かった人に投票
            most_voted = util.max_frequent_2(self.talk_vote_list, self.decide_vote_cand(), 1)
            return most_voted
        else:
            return self.SP_target

    def finish(self):
        return None

    def decide_vote_cand(self):
        #    printする場合は、print_onをTrueに変更
        print_on = False
        if print_on: print("Possessed:decide_vote_cand:start")

        # (1)talk_vote_listの最多得票者に自分以外のCOsCOmが含まれていたらそいつを返す
        if max_frequent(self.talk_vote_list) & self.alive\
                & (self.COs | self.divineders | set(self.COm)) - {int(self.base_info['agentIdx'])}:
            target = max_frequent(self.talk_vote_list) & self.alive\
                & (self.COs | self.divineders | set(self.COm)) - {int(self.base_info['agentIdx'])}
            if print_on: print("Possessed:周りに怪しまれてるCOs,divineders,COm:", target)
            return target

        # (2)自分が黒だしした人がいたら、そいつに投票
        if self.kurodashi & self.alive:
            target = self.kurodashi & self.alive
            if print_on: print("Possessed:自分の黒だし:", target)
            return target

        # (3)自分以外の占い師が出した黒だされがいた場合、
        #    そいつを守るために、例外的に、そいつと自分を除いて生きているエージェント全員を返す
        #    その中から最多得票者に投票(この処理はvoteで行う)
        black_cand = set()
        for key in self.divineders - self.fake_divineders - {int(self.base_info['agentIdx'])}:
            black_cand |= self.result_all_divineders[key]['black']
        if black_cand:
            target = self.alive - black_cand - {int(self.base_info["agentIdx"])}
            if print_on: print("Possessed:自分以外の黒だされを守るための投票:", target)
            return target

        # (4)自分の出した白だし・divineders・COm・自分以外の生きているグレーから投票
        target = self.alive - self.divineders - self.shirodashi - set(self.COm[:1])
        if target:
            if print_on: print("Possessed:自分の白だし,divineders,COm,自分以外の生きているグレー:", target)
            return target

        # (5)生きているdivindersから自分を除いた集合を返す
        if self.divineders - {int(self.base_info['agentIdx'])} & self.alive:
            target = self.divineders - {int(self.base_info['agentIdx'])} & self.alive
            if print_on: print("Possessed:自分以外の生きているdivinders:", target)
            return target

        # (6)生きている自分の白だしの集合を返す
        if self.shirodashi & self.alive:
            target = self.shirodashi & self.alive
            if print_on: print("Possessed:生きている自分の白だし:", target)
            return target

        # (7)生きているCOm[:1]の集合を返す
        if set(self.COm[:1]) & self.alive:
            target = set(self.COm[:1]) & self.alive
            if print_on: print("Possessed:生きているCOm[:1]:", target)
            return target

        # (8)自分以外の生きている人の集合を返す
        target = self.alive - {int(self.base_info['agentIdx'])}
        if print_on: print("Possessed:自分以外の生きている人:", target)
        return target

    """
    def decide_divine_cand(self):
        # divine_cand
        # 以下全て生きている前提
        # 占い候補の選定
        # 中で使われているCOsは全てdivinedersに置き換えていいんじゃないかと思ってるono

        # 0日目の処理
        if not self.base_info['day']:
            # print("divine_cand start!!")
            # print("agent_num:", self.base_info["agentIdx"])
            # print("day:", self.base_info['day'])
            return self.alive - {int(self.base_info['agentIdx'])}

        # 全体でのグレー(生きていて占われていない人)からdivinedersをのぞく
        # 優先的に占いたい人の集合
        cand = self.greys - self.divineders - self.COs

        # 確認のためのprint文
        # print("")
        # print("divine_cand start!!")
        # print("agent_num:", self.base_info["agentIdx"])
        # print("day:",self.base_info['day'])
        # print("alive:", self.alive)
        # print("greys:", self.greys)
        # print("COm:", self.COm)
        # print("COg:", self.COg)
        # print("divineders:", self.divineders)
        # print("vote_list:", self.vote_list)
        # print("exed_players:", self.exed_players)
        # print("fake_divineders:", self.fake_divineders)
        # print("result_seer['white']:", self.result_seer['white'])
        # print("result_seer['black']:", self.result_seer['black'])
        # print("result_all_divineders:", self.result_all_divineders)

        # もし霊能者COが1人しかいなければ、占い候補からは外す
        if len(self.COm) == 1:
            cand -= set(self.COm)
        # 霊能者COが複数でていた場合、その中に一人でも生き残っていたら、その中から優先される1人を選ぶ
        # 例えば、COm==[a,b,c,d,e]である時、b,c,d,e,aの順で先に該当した1人のみ、占い候補に入れられる
        if len(self.COm) >= 2 and len(set(self.COm) & cand) >= 1:
            # print("霊能CO複数のパターン")
            for i in self.COm[1:]:
                if i in cand:
                    return {i}
            return {self.COm[0]}
        # 狩人COが複数でていた場合、その中に一人でも生き残っていたら、その中から選ぶ
        if len(self.COg) >= 2 and len(self.COg & cand) >= 1:
            # print("狩人CO複数のパターン")
            return self.COg & cand
        # “他の占い師から確定偽占い師を引いた集合”からの黒だされがいて、かつ自分がまだそいつらを占っていなければそいつらの集合を返す
        if self.divineders - self.fake_divineders:
            may_black = self.alive - self.result_seer['white'] \
                        - self.result_seer['black'] - {self.base_info['agentIdx']}
            for key in self.divineders - self.fake_divineders:
                may_black &= self.result_all_divineders[key]['black']
            if may_black:
                # print("他の占い師が黒だしした人がいたパターン")
                return may_black
        # vote_meの初期化
        vote_me = set()
        for i in range(15):
            # 投票した先に自分のエージェント番号があれば、投票元をvote_meに入れる
            if self.vote_list[i] == int(self.base_info["agentIdx"]):
                vote_me.add(i + 1)
        # 自分に投票しており、かつ全体のグレーであるエージェントがいれば、その中から選ぶ
        if len(vote_me & cand) >= 1:
            # print("自分に投票した全体グレーがいたパターン")
            return vote_me & cand
        # vote_maxの初期化
        vote_max = set()
        for i in range(15):
            # 投票した先に前日処刑されたエージェント番号があれば、投票元をvote_maxに入れる
            if self.vote_list[i] == self.exed_players[-1]:
                vote_max.add(i + 1)
        if self.base_info['day'] <= 3:
            # 3日目までは、全体のグレーであり、かつ前日の処刑者に投票したエージェントがいたら、その中から選ぶ
            if len(vote_max & cand):
                # print("3日目までで前日処刑された人に投票した全体グレーがいたパターン")
                return vote_max & cand
        else:
            # 4日目以降は、全体のグレーであり、かつ前日の処刑者に投票していないエージェントがいたら、その中から選ぶ
            if len(cand - vote_max):
                # print("4日目以降で前日処刑された人に投票していない全体グレーがいたパターン")
                return cand - vote_max
        # グレーがいなかったら、自分を除いた生きているエージェントの中で、前日の処刑者に投票していないエージェントを候補として返す
        if cand:
            # print("candをそのまま")
            return cand
        if (self.divineders | self.COs) & self.alive:
            return (self.divineders | self.COs) & self.alive
        if set(self.COm) & self.alive:
            # print("生きてるCOm")
            return set(self.COm) & self.alive
        # print("生きてるエージェント")
        return self.alive - {int(self.base_info['agentIdx'])}
    
    """

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
        max_cand = set()               # 最多票獲得エージェントを格納する set を用意
        sorted_res = collections.Counter(l).most_common()
        max_vallot = sorted_res[0][1]  # 最多獲得票数
        max_cand.add(sorted_res[0][0]) # 最多票獲得エージェントの 1 つめを格納

        # 2 つめ以降は，もし最大票数を獲得しているエージェントがあれば追加，そうでなければ探索終了
        for i in range(1, len(sorted_res)):
            if(sorted_res[i][1] == max_vallot):
                max_cand.add(sorted_res[i][0])
            else:
                break

        # choose_agent = random.sample(max_cand, 1)
        # print("max_cand:",max_cand)
        return max_cand

# 前日の自分の黒出しに投票した人
# indexリストおよびその対象番号を入力すると，該当者の集合を返してくれる関数
def YMBV(l, p):
    QP = set()
    for i in range(len(l)):
        if p == l[i]:
            QP_parse = i + 1
            QP.add(QP_parse)
    return QP
