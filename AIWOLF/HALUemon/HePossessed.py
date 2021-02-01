#!/usr/bin/env python
# coding: utf-8
# author: HALU Taichi Hosoi
# Possessed 5 sub class
# ┏━━┓
# ┃ ━┫
# ┣━┓┃
# ┗━━人村

from __future__ import print_function, division

import random

import textgenerator
import emotion
import parse_content

class PossessedBehavior(object):
    def __init__(self, agent_name):
        # myname
        self.myname = agent_name

        # input and output
        # self.interpreter = interpreter.Interpreter()
        self.gen = textgenerator.TextGenerator()

        # other variables

    def getName(self):
        return self.myname

    def initialize(self, base_info, diff_data, game_setting):
        self.base_info = base_info
        self.game_setting = game_setting

        # seed設定
        random.seed(random.random() + self.base_info["agentIdx"])

        self.myrole = base_info["myRole"]
        self.result_seer = []
        self.result_med = []
        self.player_size = len(self.base_info["remainTalkMap"].keys())
        self.talk_turn = 0
        self.honest = False
        self.divined_as_wolf = []
        self.divined_as_human = []
        self.wrong_divine = set()
        self.white = set()
        self.black = set()
        self.greys = set()
        self.check_alive()
        self.seers = set()
        self.tryingPP = set()
        self.greys = set(self.alive) - {int(base_info["agentIdx"])}
        self.players = self.greys.copy()
        self.whisper_turn = 0
        self.attack_success = True
        self.attacked_who_lastnight = 0
        self.gen.gameInitialize(self.base_info["agentIdx"], self.player_size)
        #self.q = [] # 廃止しました
        self.seer_divined_me_as_werewolf = set()
        self.estimated_me_as_werewolf = set()
        self.estimated_me_as_human = set()
        self.asked_why_divine = set()
        self.asked_why_doubt = set()
        self.PPmode = False
        self.when_declare = random.randint(4, 8)
        self.emo = emotion.Emotion(self.alive)
        self.stealth = False if random.random() < 0.75 else True
        self.who_said_black = dict(zip(self.alive, [[] for i in self.alive]))
        self.has_CO_seer = False
        self.emo.myrole_appearance = base_info["myRole"]
        self.emo.myrole = base_info["myRole"]
        #print("GREYS: ", self.greys)

    def update(self, base_info, diff_data, request):
        # print("UPDATE CALLED")
        self.base_info = base_info
        self.diff_data = diff_data

        self.check_alive()

        if self.base_info["day"] == 0:
            return

      #  for i in self.diff_data.iterrows():
       #     if i[1]["type"] == "talk":
        #        self.talk_turn = i[1]["turn"] + 2

        # 投票情報
        for i in range(diff_data.shape[0]):
            if diff_data.type[i] == 'vote':
                who = diff_data.idx[i]
                to = diff_data.agent[i]
                # print("VOTE DETECTED", who, "->", to)
                # 自分に投票してきたら覚えておく
                if to == self.base_info["agentIdx"]:
                    self.emo.add(who, "voted_me")
                # 自分の投票範囲外に投票した奴は覚えておく
                elif to not in self.vote_cand():
                    self.emo.add(who, "voted_who_i_love")
                else:
                    self.emo.add(who, "voted_who_i_hate")

            if diff_data.type[i] == "execute":
                # 黒もらいが処刑されたら黒だしした奴の評価を下げる
                for seer in self.who_said_black[diff_data.agent[i]]:
                    self.emo.add(seer, "you_said_black_but_not")
                # print(self.emo.emotion)
                # raise KeyError

        for i in self.diff_data.iterrows():
            self.talk_recognize(i, request)

        # 占い結果その2
        if request == "DAILY_INITIALIZE":
            for i in range(diff_data.shape[0]):
                if diff_data["type"][i] == "divine":
                    self.result_seer.append(diff_data["text"][i])
                    self.greys -= {int(diff_data["text"][i][14:16])}
                    # print("SEER.GREYS:", self.greys)

                if diff_data["type"][i] == "identify":
                    self.result_med.append(diff_data["text"][i])
                if diff_data["type"][i] == "attack":
                    self.attacked_who_lastnight = diff_data["agent"][i]
                    # print(self.attacked_who_lastnight)

    def talk_recognize(self, i, request):
        # print("+++++++++++++i+++++++++")
        # print(i)
        # print("+++++++++++++i+++++++++")
        # who, to, interpreted, raw = self.interpreter.interpret(i[1])
        to = 0
        raw = ""
        line = i[1]
        parsed_list = parse_content.parse_text(line["text"])
        who = line["agent"]
        stattype = line["type"]
        for interpreted in parsed_list:
            try:
                self.talk_recognize_update(i, to, raw, line, who, interpreted, stattype)
            except Exception:
                print("exception")

            content = interpreted.split()
            # 占い結果その１
            if request == "DAILY_INITIALIZE" and content[0] == "DIVINED":
                # print("DIVINED IN DAILY")
                if content[2] == "WEREWOLF":
                    self.divined_as_wolf.append(int(content[1][6:8]))
                    self.emo.add(int(content[1][6:8]), "divined_as_werewolf")
                elif content[2] == "HUMAN":
                    self.divined_as_human.append(int(content[1][6:8]))
                    self.emo.add(int(content[1][6:8]), "i_divined_as_human")
                # print("SEER.DIVINED", self.divined_as_human,
                #       self.divined_as_wolf)

    def talk_recognize_update(self, i, to, raw, line, who, interpreted, stattype):
        if(stattype == "talk"):
            content = interpreted.split()
            if len(content) > 1:
                if not content[1].startswith("Agent"):
                    return
                    #content = content[1:]
                to = int(content[1][6:8])
            # print(who, to, interpreted, )
            if interpreted == "" or interpreted == "NONE":
                print(interpreted)
                print("failed to interpret:", raw)
                return
            # 発言内容からVILLAGER以外のカミングアウトを見つけてグレーリストから削除
            if content[0] == "COMINGOUT":
                #if self.talk_turn < 3:
                # 異常AgentNo対策
                if int(content[1][6:8]) > self.player_size:
                    return
                # 村人はだめ
                if content[2] == "VILLAGER":
                    return

                if content[2] in ["POSSESSED", "WEREWOLF"]:
                    self.tryingPP.add(int(i[1]["agent"]))

                if content[2] == "SEER":
                    self.seers.add(int(i[1]["agent"]))

                # 狼CO者への反応
                # if self.day == 2 and content[2] == "WEREWOLF":
                #     if self.PPmode == True:
                #         self.q.append(self.gen.generate(
                #             "received_WOLF_CO_as_PP", [int(content[1][6:8])]))
                #     else:
                #         self.q.append(self.gen.generate(
                #             "received_WOLF_CO_as_nonPP", [int(content[1][6:8])]))

                self.greys -= {int(content[1][6:8])}
                # 発言内容から占い情報を見つけて、グレーリストから削除
            if content[0] == "DIVINED":
                # COは2ターン目までに済ませるはず
                #if self.talk_turn < 3:

                # 異常AgentNo対策
                if int(content[1][6:8]) > self.player_size:
                    return
                # print("GREY LIST REMOVED", {int(content[1][6:8])})
                # print(self.greys)
                self.greys -= {int(content[1][6:8])}

                # 自分が役職持ちなのにCOした他の占いは減点
                if self.has_CO_seer:
                    self.emo.add(who, "seems_to_be_fake_seer")

                # 占い結果：人間
                if content[2] == "HUMAN":
                    # 自分に白出ししてきたやつは覚えておく
                    if int(content[1][6:8]) == self.base_info["agentIdx"]:
                        self.emo.add(who, "divined_me_human")
                        # if self.myrole == "VILLAGER" or (self.myrole == "WEREWOLF" and self.stealth == True):
                        #     self.q.append(
                        #         self.gen.generate("thankSEER", [who]))
                    self.white.add(int(content[1][6:8]))
                    # print("WHITE", self.white)
                    if self.base_info["day"] == 1 and int(content[1][6:8]) == self.base_info[
                        "agentIdx"] and self.myrole == "WEREWOLF":
                        # 狼なのに白丸出してきたやつは間違ってる(初日のみ適用)
                        self.wrong_divine.add(int(i[1]["agent"]))
                        # print("wrongdivine_bywhite", self.wrong_divine)
                # 占い結果：狼
                else:
                    # 自分に黒出ししてきたやつは覚えておく
                    if int(content[1][6:8]) == self.base_info["agentIdx"]:
                        self.seer_divined_me_as_werewolf.add(who)
                        self.emo.add(who, "divined_me_werewolf")
                        # print(
                        #     "Divined as werewolf", self.base_info["agentIdx"], self.seer_divined_me_as_werewolf)

                    self.black.add(int(content[1][6:8]))
                    self.emo.add(
                        int(content[1][6:8]), "divined_as_werewolf")
                    self.who_said_black[int(content[1][6:8])].append(who)

                    if self.base_info["day"] == 1 and self.player_size == 5 and int(content[1][6:8]) != self.base_info[
                        "agentIdx"] and self.myrole == "WEREWOLF":
                        # 狼なのにそれ以外に●出したやつも間違ってる(初日のみ適用)
                        self.wrong_divine.add(int(i[1]["agent"]))
                        # print("wrongdivine_byblack", self.wrong_divine)

                # 初日COしたもののみ占い認定
                if self.base_info["day"] == 1:
                    self.seers.add(int(i[1]["agent"]))
                    self.emo.add(who, "seems_to_be_true_seer")
                    # print("NOW SEERS", self.seers)

            # 自分の発言は無視
            if who == self.base_info["agentIdx"]:
                # print("my talk, ignored.", raw)
                return
            else:
                # 怪しまれたら覚えておく
                if content[0] == "ESTIMATE" and content[2] == "WEREWOLF":
                    if int(content[1][6:8]) == self.base_info["agentIdx"]:
                        self.emo.add(who, "estimated_me_werewolf")
                        self.estimated_me_as_werewolf.add(who)

                # 信じられたら喜ぶ
                if content[0] == "ESTIMATE" and content[2] == "HUMAN":
                    if int(content[1][6:8]) == self.base_info["agentIdx"] and self.base_info["day"] == 1:
                        self.emo.add(who, "estimated_me_human")
                        if random.random() < 0.8:
                            self.estimated_me_as_human.add(who)

                # 占い師だと予想されたら喜ぶ
                # if content[0] == "ESTIMATE" and content[2] == "SEER":
                #     if int(content[1][6:8]) == self.base_info["agentIdx"] and self.has_CO_seer and self.PPmode == False:
                #         self.q.append(self.gen.generate(
                #             "thankESTIMATE_SEER", [who]))

                # 自分宛てのアンカーで何か飛んできた時
                if to == self.base_info["agentIdx"]:

                    # 理由を聞かれたら答える
                    if content[0] == "ASK_WHY_DOUBT":
                        self.asked_why_doubt.add(
                            (int(i[1]["agent"]), int(content[1][6:8])))
                    if content[0] == "ASK_WHY_DIVINE" and self.has_CO_seer:
                        self.asked_why_divine.add(
                            (int(i[1]["agent"]), int(content[1][6:8])))

                    # 投票依頼が来たら答える
                    if content[0] == "REQUEST_VOTE":
                        # print("received REQ, VOTECAND:",
                        #       self.base_info["agentIdx"], self.vote_cand(), content[1])
                        if int(content[1][6:8]) in self.vote_cand():
                            # self.q.append(self.gen.generate("agree_vote", [who, int(content[1][6:8])]))
                            self.emo.add(
                                int(content[1][6:8]), "requested_vote")
                            self.emo.add(who, "sync_vote")
                        else:
                            # 自分への投票依頼（？）は無視
                            if who == self.base_info["agentIdx"]:
                                pass
                            if int(content[1][6:8]) == self.base_info["agentIdx"]:
                                pass
                            else:
                                # self.q.append(self.gen.generate(
                                #     "disagree_vote", [who, int(content[1][6:8])]))
                                self.emo.add(who, "desync_vote")

    def dayStart(self):
        self.talk_turn = 0
        self.whisper_turn = 0
        #self.q.clear() # 廃止しました
        self.day = self.base_info["day"]
        self.check_alive()
        # print("ALIVE", self.alive)
        # print("GREYS", self.greys)

        return None

    def grey_random(self):
        """
        グレラン
        """
        if len(self.greys) == 0:
            # print("greys is empty, chosen from alive_without_me.")
            # 自分以外の誰か
            # print("GREY RANDOM:", self.alive_without_me)
            return int(random.choice(list(self.alive_without_me)))
        # グレーから誰か
        # print("GREY RANDOM:", self.greys)
        # print("i am", self.base_info["agentIdx"], "greys are", self.greys)
        t = int(random.choice(list(self.greys)))
        # print("CHOSEN:", t)
        return t

    def check_alive(self):
        """
        生存者の確認
        """
        self.alive = []

        """
        # print("CHECKALIVE:", self.base_info)
        for i in range(self.player_size):
            # 1-origin
            i += 1
            if self.base_info["statusMap"][str(i)] == "ALIVE":
                self.alive.append(int(i))
        """
        for i in self.base_info["remainTalkMap"].keys():
            if self.base_info["statusMap"][i] == "ALIVE":
                self.alive.append(int(i))

        self.alive_without_me = list(
            set(self.alive) - {int(self.base_info["agentIdx"])})

        self.greys = self.greys & set(self.alive_without_me)
        # print("prevalive:", self.alive, self.greys, self.alive_without_me)
        self.gen.check_alive(self.alive)

    def talk(self):

        self.talk_turn += 1

        # print("TRK,GREYS:", self.greys)
        # print("TRK,ALIVE:", self.alive)

        self.check_alive()
        #print("+++TALK+++", self.myrole)
        #print(self.alive_without_me)

        # 確率系
        # 予め決定しておいたターンになったらVOTE宣言
        print("TALKTURN", self.talk_turn, self.when_declare)

        #if self.day == 1 and self.talk_turn == 5:  # and self.talk_turn == self.when_declare or self.day >= 2 and self.talk_turn == self.when_declare // 2:
            #print(self.talk_turn, "==", self.when_declare)
            #self.q.append(self.gen.generate("declare_VOTE", [self.vote()]))

        # 1日目発言
        # COするか否かで大きく変わるだろう
        if self.day == 1:

            if self.talk_turn == 1 :
                return self.gen.generate("comingout_SEER")
                self.has_CO_seer = True
                self.emo.myrole_appearance = "SEER"
            # 黒を引いた占いは正直に
            #if len(self.result_seer) > 0 and len(self.divined_as_wolf) > 0:
            #    return self.gen.generate("divine_WEREWOLF", [int(self.result_seer.pop()[14:16])])
            # 白を引いた占いと人外は黒凸
            # 人外は確率で白を出しても良い
            if self.talk_turn == 2:
                tar = self.grey_random()
                if  len(self.seers) <3 :
                    self.emo.add(tar, "i_divined_as_werewolf(fake)")
                    self.divined_as_wolf.append(tar)
                    return self.gen.generate("divine_WEREWOLF", [tar])
                else:
                    self.emo.add(tar, "i_divined_as_human(fake)")
                    return self.gen.generate("divine_HUMAN", [tar])
            if self.talk_turn <6:
                #print(self.talk_turn, "==", self.when_declare)
                if len(self.seers) == 1 :
                    return self.gen.generate("declare_VOTE", [self.vote()])
                elif len(self.seers) == 2 :
                    return self.gen.generate("declare_VOTE", self.divined_as_wolf)
                else:
                    return self.gen.generate("declare_VOTE", list(self.seers-{int(self.base_info["agentIdx"])}))

        # 2日目
        # こっちもCO者か否かで変わってくる
        # が、それ以前にもし役職持ち全生存だった場合は生き残りが真狼狂の可能性が極めて高いため
        # 必ずPP宣言をする
        if self.day == 2:
            # 役職持ち生存確認
            #print("seers,alives", self.seers, self.alive)
            if self.talk_turn == 1:
                # 役職関係なくPP宣言
                return self.gen.generate("comingout_POSSESSED")
            if self.talk_turn < 6:
                if len(self.seers & set(self.alive_without_me)) == 1:
                    if len(self.seers)==2:
                        return self.gen.generate("declare_VOTE",list(self.seers & set(self.alive_without_me)))
                    else:
                        return self.gen.generate("declare_VOTE",[self.grey_random()])
                else:
                    tar = random.choice(self.alive_without_me)
                    return self.gen.generate("declare_VOTE",[tar])


        return "Over"
                #    if self.seers <= set(self.alive) and self.myrole not in ["VILLAGER"]:
                #        self.PPmode = True
                #        self.emo.myrole_appearance = "POSSESSED"
                    #    self.emo.enter_ppmode()
                            # return self.gen.generate("comingout_POSSESSED" if random.random() > 0.5 else "comingout_WEREWOLF")
                        #elif self.talk_turn <= 3:
                        #    self.q.append(self.gen.generate("tweet_POSSESSED"))

                    #else:
                    #    if self.talk_turn == 1:
                            # 村人は２日目１ターン目のあいさつ
                    #        if self.PPmode == False and (
                    #                self.myrole in ["VILLAGER"] or self.myrole == "WEREWOLF" and self.stealth == True):
                    #            return self.gen.generate("d2t1")
                    #        else:
                                # 占いは結果報告
                    #            if self.myrole in ["SEER"]:
                    #                if len(self.result_seer) > 0:
                    #                    res = self.result_seer.pop(-1)
                    #                    if "WEREWOLF" in res:
                    #                        return self.gen.generate("divine_WEREWOLF", [int(res[14:16])])
                    #                    else:
                    #                        return self.gen.generate("divine_HUMAN", [int(res[14:16])])
                                # 狂人や狼は白だし
                    #            elif (len(self.greys)) > 0:
                    #                tar = self.grey_random()
                    #                self.emo.add(tar, "i_divined_as_human(fake)")
                    #                return self.gen.generate("divine_HUMAN", [tar])
                    #            else:
                    #                tar = random.choice(self.alive_without_me)
                    #                self.emo.add(tar, "i_divined_as_human(fake)")
                    #                return self.gen.generate("divine_HUMAN", [tar])

                # 確定白がいた場合
                # print("確定白？", self.white, self.seers)
                #if self.day == 1:
                #    if len(self.white) == 1 and len(self.black) == 0 and len(self.seers) >= 2 and self.talk_turn == 3:
                #        if self.base_info["agentIdx"] not in self.white:
                #            self.q.append(self.gen.generate(
                #                "white_by_all", list(self.white)))
                #    if len(self.black) == 1 and len(self.white) == 0 and len(self.seers) == 2 and self.talk_turn == 3:
                #        if self.base_info["agentIdx"] not in self.black:
                #            self.q.append(self.gen.generate(
                #                "black_by_all", list(self.black)))
                #    if len(self.black) > 2 and self.talk_turn == 3:
                #        self.q.append(self.gen.generate("black>2", list(self.black)))
                #    if len(self.black) == 0 and len(self.seers) == 2 and self.talk_turn == 3:
                #        self.q.append(self.gen.generate("black=0", list(self.black)))

                #if self.talk_turn == 4:
                #    loveest = self.emo.loveest(self.alive_without_me)
                #    vote = self.vote()
                    # if True:
                    #    self.q.append(">>Agent[01] 誰が狂人かな。")
                #    if random.random() < 0.5 or loveest == vote:
                #        self.q.append(self.gen.generate("ask_WHO_LIKE_WOLF",
                #                                        [self.emo.loveest(self.alive_without_me)]))
                #    else:
                #        self.q.append(self.gen.generate("ask_HOW_DO_YOU_FEEL",
                #                                        [loveest, vote]))

                # 最後にキューの健康さを保証する
                # キューに何もなかったらover
                # 低確率で意味のないつぶやき
                #if len(self.q) > 1:
                #    self.q = self.q[:1]
                #if len(self.q) == 0:
                #    if len(self.alive) in [4, 5] and self.talk_turn <= 3 and random.random() < 0.7:
                #        return self.gen.generate("execute_remaining_2")
                #    if len(self.alive) <= 3 and self.talk_turn <= 3 and random.random() < 0.7:
                #        return self.gen.generate("execute_remaining_1")
                #    if random.random() < 0.8 and self.talk_turn <= 5 and self.PPmode == False:
                #        cand = set(self.alive_without_me) - set(self.vote_cand())
                #        if len(cand) > 0:
                #            nakayosi = self.emo.loveest(cand)
                #            return self.gen.generate("trust_who", [nakayosi, self.vote()])
                #    return "Over" if random.random() < 0.9 else self.gen.generate("tweet",
                #                                                                  [self.emo.loveest(self.alive_without_me)])
                #return self.q.pop(-1)

    def vote(self):
        """
        vote候補者でloveが最低の者に投票
        """
        # print("VOTE THINKING",self.base_info["agentIdx"], self.vote_cand())
        return self.emo.hateest(self.vote_cand())

    def vote_cand(self):
        COs = self.seers & set(self.alive_without_me)
        non_COs = set(self.alive_without_me) - self.seers - set(self.divined_as_human)
        if self.day == 1:
            if len(self.seers) == 1:
                return set(self.divined_as_wolf)
            # 2CO状態なら
            elif len(self.seers) == 2:
                return COs
            else:
                return non_COs
        # 2日目以降はPPを考慮
        if self.day >= 2 :
            if len(COs) == 0:
                if len(self.tryingPP - set([self.base_info["agentIdx"]])) == 1:
                    #print("PPvote")
                    cand = set(self.alive_without_me) - set(self.tryingPP)
                    #print(self.alive, self.tryingPP, cand)
                #    if len(cand) > 0:
                    return cand
                else:
                    return set(self.alive)
            if len(COs) == 1:
                if len(self.seers) == 2:
                    return COs
                else:
                    return non_COs
            else:
                if len(self.tryingPP - set([self.base_info["agentIdx"]])) == 1:
                    #print("PPvote")
                    cand = set(self.alive_without_me) - set(self.tryingPP)
                    #print(self.alive, self.tryingPP, cand)
                #    if len(cand) > 0:
                    return cand
                else:
                    return set(self.alive)

                #if self.base_info["day"] == 2:
                #if self.myrole == "POSSESSED":
                #cand =self.alive_without_me & self.seers
                #if len(cand) > 0:


        # 2日目で、自分が占いで、狼を引いてて、そいつが生存してるならそいつに
        #if len(set(self.divined_as_wolf) & set(self.alive)) > 0:
        #    return set(self.divined_as_wolf) & set(self.alive)

        # 村人の特殊投票
    #    if self.myrole in ["VILLAGER", "SEER"]:
            # 2CO状態なら、その中に狼はいないものとする
    #        if len(self.seers) < 3:
                # 全員から黒が出てるやつはつる
    #            if len(self.black & set(self.alive_without_me)) == 1:
    #                return self.black & set(self.alive_without_me)

    #            if len(non_COs) > 0:
    #                return non_COs
            # 3COより多い状態なら、その中に狼がいるものとする
    #        else:
    #            print("CO >=3, so choose from COs.", COs)
    #            if len(COs) > 0:
    #                return COs

        # 狼と狂人のための特殊投票
    #    if self.myrole in ["POSSESSED", "WEREWOLF"]:
    #        print("I am", self.myrole, self.base_info["agentIdx"])
    #        print("seers,alive", self.seers, self.alive_without_me)
    #        print("COs,nonCOs", COs, non_COs)
            # 感情に委ねる
            #return set(self.alive) - set([self.base_info["agentIdx"]])

            # 1CO状態なら人狼は必ずCOするので真占いがCOしていないパラダイス
                # 自分が狂人なら可能な限りCO済みの者に
            #    if self.myrole == "POSSESSED" and len(COs) > 0:
            #        return COs
                # 狼は狂人への投票を回避
            #    elif self.myrole == "WEREWOLF" and len(non_COs) > 0:
            #        return non_COs
            # 3CO状態なら
            #else:
                # 自分が狂人なら可能な限りCOしていない者に
            #    if self.myrole == "POSSESSED" and len(non_COs) > 0:
            #        return non_COs
                # 狼は狂人への投票を回避
            #    elif self.myrole == "WEREWOLF" and len(non_COs) > 0 and self.seers <= set(self.alive):
            #        return non_COs
                # ただし、COが一人でも欠けてたらそこに狂人はいないだろう
            #    else:
            #        return COs

    #    if self.myrole in ["WEREWOLF", "POSSESSED"]:
    #        cand = set(self.alive_without_me) - self.wrong_divine
    #        if len(cand) > 0:
                # 可能なら間違い占い師以外に投票したい
    #            print("AVOIDED WRONG DIVINE", self.wrong_divine)
    #            return cand
    #        return self.alive_without_me
        # 万が一占いだったら、白丸引いたやつに投票してはいけない
    #    cand = list(set(self.alive_without_me) - set(self.divined_as_human))
    #    if self.player_size == 15:
    #        return cand
    #    return cand

    def attack(self):
        """
        可能な限りCO者以外の白もらいを
        """
        COs = self.seers & set(self.alive_without_me) - \
              {self.attacked_who_lastnight}
        white_cand = set(self.alive_without_me) & self.white - \
                     self.seers - {self.attacked_who_lastnight}
        non_COs = set(self.alive_without_me) - self.seers - \
                  {self.attacked_who_lastnight}

        # 可能な限り無CO者を
        if len(non_COs) > 0:
            return random.choice(list(non_COs))

        # いないならランダム
        return self.grey_random()

    def divine(self):
        """
        可能な限りグレーから
        """
        self.check_alive()
        #print("DIVINE")
        #print("ALIVE:", self.alive_without_me)
        #print("GREYS", self.greys)
        # print(self.base_info)
        return self.grey_random()

    def finish(self):
        if self.base_info["agentIdx"] == 1:
            pass
            # self.interpreter.show_failed_list()
        return None
