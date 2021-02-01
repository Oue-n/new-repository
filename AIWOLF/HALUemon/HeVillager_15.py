# !/usr/bin/env python
# coding: utf-8
# author: HALU Taichi Hosoi
# villager 15 super & base class
# ┏━┳━━┓
# ┃ ┃ ━┫
# ┃ ┣━┓┃
# ┗━┻━人村

import aiwolfpy.contentbuilder as cb  # aiwolfpyからプロトコルを生成する関数を流用

import parse_content
import util

import random


class VillagerBehavior(object):  # 村人の人格クラス
    """
    村人の振る舞い
    これをあらゆる役職の基底クラスにする
    """

    def __init__(self, agent_name):  # エージェント名,完全な黒認定リスト,今日の投票先を初期化
        # myname
        self.myname = agent_name
        # 今日の投票先
        self.todays_vote = None

    def getName(self):  # 自分の名前を返すメソッド
        """
        名前を返せば良い
        """
        return self.myname

    def initialize(self, base_info, diff_data, game_setting):  # ゲーム開始時に呼ばれるメソッド
        """
        新たなゲーム開始時に一度だけ呼ばれる
        前回のゲームデータのリセット等してもいいししなくてもいい
        """
        self.base_info = base_info
        # game_setting
        self.game_setting = game_setting
        self.player_size = len(self.base_info["remainTalkMap"].keys())
        self.greys = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15}
        self.alive = {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15}

        #######################
        # RULE BASE VARIABLES #
        #######################
        self.talk_vote_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # 誰が誰に投票したのかがわかるリスト
        # 中の数字は投票先、インデックスは投票を行った人の番号－1
        self.COs = set()  # seer CO したプレーヤ集合
        self.COm = []  # medium CO したプレーヤ集合, result_all_mediumsのキーに対応
        self.COg = set()  # guard CO したプレーヤ集合
        self.COp = set()  # possessed CO したプレーヤ集合
        self.result_all_divineders = {}  # 全部の占い師の言ってることを格納する多重辞書
        self.result_all_mediums = {}     # 全部の霊媒師の言ってることを格納する多重辞書
        self.vote_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.exed_players = []  # 吊られたプレーヤを格納するリスト
        self.ated_players = []  # 噛まれたプレーヤを格納するリスト
        self.divineders = set()  # TALK 内で "DIVINED Agent[xx] HUMAN/WEREWOLF" を宣言したプレーヤ集合
                                 # result_all_divinedersのキーに対応
        self.fake_divineders = set()
        self.likely_fake_divineders = set()

        self.attack_judge = 0

        #以下，人狼のみ使用する変数一覧
        self.W_COs = set()
        self.W_COm = set()
        self.W_COg = set()
        self.W_vote_cand = set()
        self.W_attack_cand = set()

        # 残り人数7人以下になったときに使う集合
        self.under_7_vote = {0:-1}
        self.yesterday_vote_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.result_guard = set()      # 護衛成功したエージェントの集合


        #######################
        # /RULE BASE VARIABLES #
        #######################

        # print(diff_data)
        # print(base_info)

    def update(self, base_info, diff_data, request):  # 行動が行われるたびに呼ばれるメソッド
        print_on = False
        if print_on: print("REQUEST:", request)
        self.base_info = base_info
        self.diff_data = diff_data  # 基本情報と変化したデータ？を更新

        # 格納した diff_data を一行ずつ処理するために，一行ずつ i に格納していく
        for i in self.diff_data.iterrows():
            # to = 0
            line = i[1]
            # talk_recognizeにこれを渡す
            self.talk_recognize(i, line["type"])

        # fake_divineders の更新(1)
        # 霊媒結果と占い結果を照らし合わせて、矛盾があれば、その占い師をfake_divinedersに格納
        # 霊媒黒結果と占い白結果、霊媒白結果と占い黒結果の共通部分が存在すれば、その占い結果を出した占い師をfake_divinedersに格納
        # COmが2人以上いれば、最初の2人分の霊媒結果の共通部分を、霊媒結果として考える
        # COmが1人の時は、占い黒結果の中に霊媒師(1人)がいたら、その占い師をfake_divinedersに格納
        if self.COm:
            # 自分以外の占い師がいればCO_Seerにはいる
            for CO_seer in list(self.divineders - {int(self.base_info['agentIdx'])}):
                # 1人はそのまま素直に
                if len(self.COm) == 1:
                    if self.result_all_mediums[self.COm[0]]["black"] & self.result_all_divineders[CO_seer]["white"]:
                        self.fake_divineders.add(CO_seer)
                    if self.result_all_divineders[CO_seer]["black"] & self.result_all_mediums[self.COm[0]]["white"]:
                        self.fake_divineders.add(CO_seer)
                    if self.COm[0] in self.result_all_divineders[CO_seer]["black"]:
                        self.fake_divineders.add(CO_seer)
                # 2人以上だったら，霊能二人の共通の結果と，CO_seerの結果を考慮．矛盾があれば CO_seer をfake_divinedersに格納
                elif len(self.COm) > 1:
                    if self.result_all_mediums[self.COm[0]]["black"] & self.result_all_mediums[self.COm[1]]["black"] \
                            & self.result_all_divineders[CO_seer]["white"]:
                        self.fake_divineders.add(CO_seer)
                    if self.result_all_divineders[CO_seer]["black"] & self.result_all_mediums[self.COm[1]]["white"] \
                            & self.result_all_mediums[self.COm[0]]["white"]:
                        self.fake_divineders.add(CO_seer)

        # fake_divineders の更新(2)
        # 襲撃された人に黒だしした占い師がいたら、その占い師をfake_divinedersに格納
        if self.ated_players:
            for CO_seer in list(self.divineders - {int(self.base_info['agentIdx'])}):
                if self.result_all_divineders[CO_seer]["black"] & set(self.ated_players):
                    self.fake_divineders.add(CO_seer)

        # likely_fake_divineders (村人) の更新
        # 自分に黒だしした占い師を、likely_fake_divinedersに入れる
        if self.base_info["myRole"] == "VILLAGER":
            for CO_seer in list(self.divineders):
                if int(self.base_info['agentIdx']) in self.result_all_divineders[CO_seer]["black"]:
                    self.likely_fake_divineders.add(CO_seer)

    def dayStart(self):  # 一日の初めに呼び出されるメソッド
        self.talk_turn = 0  # 発話ターンを初期化
        self.todays_vote = None  # 今日の投票先を初期化
        # 投票宣言リスト、投票先リストの初期化
        self.talk_vote_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.yesterday_vote_list = self.vote_list[:]
        self.vote_list = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        return None  # Noneを返す(なぜ？)

    def talk(self):  # 発話内容をサーバーに送るメソッド
        if self.base_info["myRole"] == 'VILLAGER':
            self.talk_turn += 1
        # print("villagerのtalk_turn", self.base_info["day"], self.talk_turn)

        if self.talk_turn < 10:
            return cb.vote(self.vote())
            # return cb.skip()
        return cb.over()

    # 5ターン未満ならskip　以降はover (どうするかは要話し合い)

    def whisper(self):
        return cb.over()

    def vote(self):
        # vote_candに対し、他の人の投票表明が2番目多かった人に投票
        # 1% の確率で村人と同じところに投票する (細井ノイズ)

        # 投票する候補を叩き出してるだけ
        cands = self.vote_cand()

        #talk_vote_list の中から2番目の人をとってくる操作
        most_voted = util.max_frequent_2(self.talk_vote_list, cands, 0)
        return most_voted

    def vote_cand(self):
        """
        # ##### 変数まとめ #####
        # true_black            :全体目線　確定黒の集合    : divineders-fakeの占い結果から黒だしの結果の共通部分
        # my_true_black         :自分目線　確定黒の集合    : divineders-fake-likelyの占い結果から黒だしの結果の共通部分
        # divined_black         :自分目線　黒っぽい人の集合 : divineders-fake-likelyの占い結果から黒だしの結果の和集合
        # fake_divineders       :全体目線　偽占い師の集合  : r-a-dとr_a_mとの結果比較
        # likely_fake_divineders:自分目線　偽占い師の集合  : 役職によって更新方法を変える
        #                                             : 占いは自分以外のdivineders全て
        #                                             : 人狼はdivinedersの結果とはじめのwolfsの情報との矛盾が生じた人全て
        #                                             : 霊媒師は自分に黒だしをしたdivineders、divinedersの結果と自分の霊能結果との矛盾が生じた人全て
        #                                             : 村人は自分に黒だしをしたdivineders全て
        #                                             : 狩人は自分に黒だしをしたdivineders全て、護衛成功した人に黒だししたdivineders
        #                                             : 狂人は自分に自分以外のdivineders全て、別でtrue_seerを作成
        # COs                   :占いCOした人の集合      :
        # divineders            :占い結果をいった人の集合 :
        """
        #    printする場合は、print_onをTrueに変更
        print_on = False

        under_7 = False

        # (0)生き残り人数が7人以下になった場合の処理
        if under_7:
            if len(self.alive) <= 7 and self.under_7_vote:
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
                # 護衛成功した人を外す(村人ではself.result_guardは空集合になっている)
                if self.result_guard & self.under_7_vote.keys():
                    for i in self.result_guard & self.under_7_vote.keys():
                        self.under_7_vote.pop(i,None)
                # 辞書が空でなければ、最多得票者に投票した回数が多い人の集合を返す
                if len(self.under_7_vote):
                    if print_on: print("under_7_vote:", self.under_7_vote)
                    under_7_max_vote = {i[0] for i in self.under_7_vote.items()\
                                        if i[1] == max(self.under_7_vote.values())}
                    if print_on: print("under_7_max_vote:", under_7_max_vote)
                    return under_7_max_vote
                if print_on: print("under_7_vote:", self.under_7_vote)

        #    確定黒と確定白の確認
        #    生きている人から，fake_divinederを除くdivinedersの占い黒結果の共通部分を確認
        true_black = self.alive.copy()
        true_white = self.alive.copy()
        for key in self.divineders - self.fake_divineders:
            true_black &= self.result_all_divineders[key]["black"]
            true_white &= self.result_all_divineders[key]["white"]
        true_white |= self.result_guard & self.alive
        if print_on: print("true_black:", true_black)

        # (1)全体目線での確定黒がいた場合，そこに投票
        if self.divineders and true_black:
            return true_black

        fake_on = False

        # (2)確定偽占い師がいた場合そこに投票
        if fake_on:
            if self.fake_divineders:
                if print_on: print("self.fake_divineders:", self.fake_divineders)
                return self.fake_divineders

        # (3)占い結果を行った人(divineders)が３人以上いた場合、
        #    占い師が1人でも生きていて、
        #    かつ、霊能結果で黒と出された占い師が"devinedersの人数-2"未満なら、占い師に投票
        #    意味：「占い師3人以上」=「人狼が占いCOしている」なので、人狼を吊れるまで、占い師に投票を続ける
        if len(self.divineders) >= 3:
            if self.divineders & self.alive:
                # 霊媒黒結果の共通部分の確認(霊媒師は2人目まで)
                result_medium_black = set()
                if len(self.COm) == 1:
                    result_medium_black = self.result_all_mediums[self.COm[0]]["black"]
                elif len(self.COm) >= 2:
                    result_medium_black = self.result_all_mediums[self.COm[0]]["black"] \
                                          & self.result_all_mediums[self.COm[1]]["black"]
                # 霊媒結果で黒と言われてない占い師が3人以上なら、
                # その中に人狼が(おそらく)混じっているはずなので、生きている占い師の中から投票
                if len(self.divineders - result_medium_black) >= 3:
                    if print_on: print("占い師3人以上で、その中に人狼がいると思われる場合")
                    return self.divineders & self.alive

        #    may_blackの確認
        #    信用できる占い師が出した黒結果の和集合からdivinedersを除いた集合
        may_black = set()
        for key in self.divineders - self.fake_divineders - self.likely_fake_divineders:
            may_black |= self.result_all_divineders[key]['black']
        may_black -= self.divineders
        if print_on: print("may_black:", may_black)

        # (4)may_blackが生きていれば投票
        if may_black & self.alive - {int(self.base_info["agentIdx"])}:
            return may_black & self.alive - {int(self.base_info["agentIdx"])}

        not_fake_divineders_greys = self.alive.copy()
        for key in self.divineders - self.fake_divineders - self.likely_fake_divineders:
            not_fake_divineders_greys -= self.result_all_divineders[key]["black"]
            not_fake_divineders_greys -= self.result_all_divineders[key]["white"]

        # (5)自分目線でグレーな人(占われていないかつ役職持ちではない人)に投票
        my_greys = not_fake_divineders_greys - self.divineders - self.COs - set(self.COm)\
                    - true_white - {int(self.base_info["agentIdx"])}
        if print_on: print("my_greys:", my_greys)
        if my_greys:
            return my_greys

        #    それもいなければ生きている人から選ぶ
        if print_on: print("自分以外の誰かに投票")
        return self.alive - {int(self.base_info["agentIdx"])}

    def attack(self):
        return self.base_info['agentIdx']

    def divine(self):
        return self.base_info['agentIdx']

    def guard(self):
        return self.base_info['agentIdx']

    def finish(self):
        return None

    def talk_recognize(self, i, stattype):
        to = 0
        raw = ""
        line = i[1]  # {key:xxx, ["day":xxx, "type":xxx, ....]} の [] 部分が変数 line に格納されている．
        who = int(line["agent"])
        parsed_list = parse_content.parse_text(line["text"])  # diff_data の text を抽出している．

        # 格納されるものによって text の内容が変化する
        # [    type =       ]       [          text         ]
        # initialize, finish:       COMINGOUT Agent[01] SEER
        # talk, whisper:            発話文そのまま
        # vote, attack_vote:        vote 文, attack 文
        # execute, dead:            OVER
        # divine, identify, guard:  divined, identified, guard 文　DIVINED Agent[02] WEREWOLF
        # attack                    attack 文

        # parsed_list には長くとも
        # ['COMINGOUT Agent[05] VILLAGER', 'Agent[04] DIVINED Agent[05] WEREWOLF', 'ESTIMATE Agent[04] WEREWOLF', 'ESTIMATE Agent[04] POSSESSED']
        # みたいなのが入る
        # これを interpreted に 1 つずつ格納していく
        for interpreted in parsed_list:
            try:
                self.talk_recognize_update(i, to, raw, line, who, interpreted, stattype)
            except Exception:
                print("exception")

    def talk_recognize_update(self, i, to, raw, line, who, interpreted, stattype):
        # diff_data の type が talk である場合
        if stattype == "talk":
            # "day"   : 何日目に
            # "type"  : "talk"
            # "idx"   : talkの通し番号
            # "turn"  : talk_turnの番号
            # "agent" : 誰が言ったか
            # "text"  : 何を言ったか
            # interpreted: COMINGOUT Agent[05] VILLAGER
            # content = ['COMINGOUT', 'Agent[05]', 'VILLAGER']
            content = interpreted.split()
            # 2 以上であれば入る
            if len(content) > 1:
                # content[1] が "Agent" から始まらない場合
                if not content[1].startswith("Agent"):
                    # content の index 1 から末尾までの要素を取り出す
                    return
                    # content = content[1:]
                to = int(content[1][6:8])
            # print(who, to, interpreted,)

            # interpreted の中身が空である場合は失敗していると表記する
            if interpreted == "" or interpreted == "NONE":
                print("interpreted:", interpreted)
                print("failed to interpret:", raw)
                return

            # 誰が何と "CO" したのか
            if content[0] == "COMINGOUT":
                # 異常AgentNo対策
                if int(content[1][6:8]) > self.player_size:
                    print("NOT WORKING!! ERRORCODE:TALKCOCONT")
                    return
                # SEER だと CO した人リスト
                if content[2] == "SEER":
                    self.COs.add(who)
                # MEDIUM だと CO した人リスト
                if content[2] == "MEDIUM" and who not in self.COm:
                    self.COm.append(who)
                    self.result_all_mediums[who] = {'black': set(), 'white': set()}
                # BODYGUARD だと CO した人リスト
                if content[2] == "BODYGUARD":
                    self.COg.add(who)
                # POSSESSED だと CO した人リスト
                if content[2] == "POSSESSED":
                    self.COp.add(who)

            # 誰が誰を何と "DIVINE" したのか
            if content[0] == "DIVINED":
                # DIVINE は 2 "ターン" 目までに済ませるはず
                if self.talk_turn < 3:
                    # 異常AgentNo対策
                    if int(content[1][6:8]) > self.player_size:
                        print("NOT WORKING!! ERRORCODE:TALKDIVCONT")
                        return
                    # DIVINE 結果を多重辞書に格納する
                    # DIVINED を過去に宣言したことがある場合
                    if who in self.divineders:
                        # 占いの結果が HUMAN であった場合 key= 'white' に対象を格納
                        if content[2] == 'HUMAN':
                            self.result_all_divineders[who]['white'].add(to)
                            # print("self.result_all_divineders1",self.result_all_divineders)
                            self.greys -= {to}
                        # 占いの結果が WEREWOLF であった場合 key= 'black' に対象を格納
                        elif content[2] == 'WEREWOLF':
                            self.result_all_divineders[who]['black'].add(to)
                            # print("self.result_all_divineders2",self.result_all_divineders)
                            self.greys -= {to}
                    # DIVINED を過去に宣言したことがない場合
                    else:
                        # divineders 集合にこれを追加する
                        self.divineders.add(who)
                        # divineders 辞書を初期化する
                        self.result_all_divineders[who] = {'black': set(), 'white': set()}
                        # print("self.result_all_divineders3",self.result_all_divineders)
                        # 占いの結果が HUMAN であった場合 key= 'white' に対象を格納
                        if content[2] == 'HUMAN':
                            self.result_all_divineders[who]['white'].add(to)
                            # print("self.result_all_divineders4",self.result_all_divineders)
                            self.greys -= {to}
                        # 占いの結果が WEREWOLF であった場合 key= 'black' に対象を格納
                        elif content[2] == 'WEREWOLF':
                            self.result_all_divineders[who]['black'].add(to)
                            # print("self.result_all_divineders5",self.result_all_divineders)
                            self.greys -= {to}

            if content[0] == "IDENTIFIED":
                # IDENTIFIED は 2 "ターン" 目までに済ませるはず
                if self.talk_turn < 3:
                    # 異常AgentNo対策
                    if int(content[1][6:8]) > self.player_size:
                        print("NOT WORKING!! ERRORCODE:TALKIDENTCONT")
                        return
                    # IDENTIFIED 結果を多重辞書に格納する
                    # IDENTIFIED を過去に宣言したことがある場合
                    if who in self.COm:
                        # 占いの結果が HUMAN であった場合 key= 'white' に対象を格納
                        if content[2] == 'HUMAN':
                            self.result_all_mediums[who]['white'].add(to)
                        # 占いの結果が WEREWOLF であった場合 key= 'black' に対象を格納
                        elif content[2] == 'WEREWOLF':
                            self.result_all_mediums[who]['black'].add(to)
                    # DIVINED を過去に宣言したことがない場合
                    else:
                        # COm 集合にこれを追加する
                        self.COm.append(who)
                        # 辞書を初期化する
                        self.result_all_mediums[who] = {'black': set(), 'white': set()}
                        # 占いの結果が HUMAN であった場合 key= 'white' に対象を格納
                        if content[2] == 'HUMAN':
                            self.result_all_mediums[who]['white'].add(to)
                        # 占いの結果が WEREWOLF であった場合 key= 'black' に対象を格納
                        elif content[2] == 'WEREWOLF':
                            self.result_all_mediums[who]['black'].add(to)

                    # 辞書型の宣言
                    # dict = {'key1': 'value1', 'key2': 'value2'}
                    # dict['key1'] = {'key1_1': 'value1_1', 'key2_1': 'value2_1'}

            # 誰が誰に "VOTE" するつもりなのか(宣言が聞きたい)
            # vote = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]　で初期化して
            # それぞれの index を agentID を結びつけて，対象を格納する
            if content[0] == "VOTE":
                # 異常AgentNo対策
                if int(content[1][6:8]) > self.player_size:
                    print("NOT WORKING!! ERRORCODE:TALKVOTECONT")
                    return
                # self.vote_list.append([who, content[1][6:8]])
                # [0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  0,   0,  0,  0, 0] (1~15 の"IDxを"格納する)
                # ↑　↑   ↑　↑　↑　↑　↑　↑　 ↑　↑  　↑　 ↑   ↑　  ↑  ↑
                # [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15]　(index は "Agent" である 1~15 を想定する
                # 異常対策
                if 1 <= who and who <= 15:
                    if who == int(self.base_info["agentIdx"]):
                        return
                    self.talk_vote_list[who - 1] = int(content[1][6:8])
                else:
                    print("NOT WORKING!! ERRORCODE:TALKVOTECONT2")

            # 自分の発言は無視
            if who == self.base_info["agentIdx"]:
                # print("my talk, ignored.", raw)
                return

        # diff_data の type が vote である場合
        elif stattype == "vote":
            # "day"   : 何日目に
            # "type"  : "vote"
            # "idx"   : 誰が投票したか
            # "turn"  : 0
            # "agent" : 誰に投票したか -> who
            # "text"  : 誰に投票したかの文
            if line['idx'] in range(1,16):
                if line['idx'] == int(self.base_info["agentIdx"]):
                    return
                self.vote_list[line['idx'] - 1] = who
                return
            print("NOT WORKING!! ERRORCODE:VOTECONT")

        # diff_data の type が execute である場合
        elif stattype == "execute":
            # エージェントの状態が executed になる
            self.exed_players.append(who)
            self.alive -= {who}
            self.greys -= {who}

        # diff_data の type が dead である場合
        elif stattype == "dead":
            # エージェントの状態が attacked になる
            self.attack_judge = 1
            self.ated_players.append(who)
            self.alive -= {who}
            self.greys -= {who}

        # diff_data の type が whisper である場合
        elif stattype == "whisper":
            # "day"   : 何日目に
            # "type"  : "talk"
            # "idx"   : talkの通し番号
            # "turn"  : talk_turnの番号
            # "agent" : 誰が言ったか
            # "text"  : 何を言ったか
            # interpreted: COMINGOUT Agent[05] VILLAGER
            # content = ['COMINGOUT', 'Agent[05]', 'VILLAGER']
            content = interpreted.split()
            # 2 以上であれば入る
            if len(content) > 1:
                # content[1] が "Agent" から始まらない場合
                if not content[1].startswith("Agent"):
                    # content の index 1 から末尾までの要素を取り出す
                    return
                    # content = content[1:]
                to = int(content[1][6:8])

            # interpreted の中身が空である場合は失敗していると表記する
            if interpreted == "" or interpreted == "NONE":
                print("interpreted:", interpreted)
                print("failed to interpret:", raw)
                return

            # 誰が何と "CO" したのか
            if content[0] == "COMINGOUT":
                # 異常AgentNo対策
                if int(content[1][6:8]) > self.player_size:
                    print("NOT WORKING!! ERRORCODE:WHISPCOCONT")
                    return
                # SEER だと CO した "人狼" 集合
                if content[2] == "SEER":
                    self.W_COs.add(who)
                # MEDIUM だと CO した "人狼" 集合
                if content[2] == "MEDIUM":
                    self.W_COm.add(who)
                # BODYGUARD だと CO した "人狼" 集合
                if content[2] == "BODYGUARD":
                    self.W_COg.add(who)

            # 他の人狼が誰に "VOTE" するつもりなのか(宣言が聞きたい)
            if content[0] == "VOTE":
                # 異常AgentNo対策
                if int(content[1][6:8]) > self.player_size:
                    print("NOT WORKING!! ERRORCODE:WHISPVOTE")
                    return
                # 異常対策
                if 1 <= who and who <= 15:
                    if who == int(self.base_info["agentIdx"]):
                        return
                    self.W_vote_cand.add(int(content[1][6:8]))
                else:
                    print("NOT WORKING!! ERRORCODE:WHISPVOTE2")

            if content[0] == "ATTACK":
                # 異常AgentNo対策
                if int(content[1][6:8]) > self.player_size:
                    print("NOT WORKING!! ERRORCODE:WHISPATT")
                    return
                # 異常対策
                if 1 <= who and who <= 15:
                    if who == int(self.base_info["agentIdx"]):
                        return
                    self.W_attack_cand.add(int(content[1][6:8]))
                else:
                    print("NOT WORKING!! ERRORCODE:WHISPATT2")
