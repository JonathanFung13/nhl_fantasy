import random
import numpy as np

debug = False

def doprint(text1, text2):
    if debug: print(text1, text2)
    return

def lottery_sim(num_ullhp_teams_in_lottery = 10, nsimulations=1000):
    odds_draw_one = [0.185, 0.135, 0.115, 0.095, 0.085, 0.075, 0.065, 0.06, 0.05, 0.035, 0.03, 0.025, 0.02, 0.015, 0.01]
    odds_draw_two = [0.165, 0.13, 0.113, 0.096, 0.087, 0.078, 0.068, 0.063, 0.053, 0.038, 0.033, 0.027, 0.022, 0.017, 0.011]
    odds_draw_three = [0.144, 0.123, 0.111, 0.097, 0.089, 0.08, 0.071, 0.067, 0.057, 0.041, 0.036, 0.03, 0.024, 0.018, 0.012]


    ullhp_standings = list(range(13))

    # Associate NHL draft odds to ULLHP teams
    ullhp_odds = []
    for i, j in enumerate(odds_draw_one):
        ullhp_odds.append(i%num_ullhp_teams_in_lottery)

    lottery_results_3up = np.zeros((13,13))
    lottery_results_chris = np.zeros((13,13))
    lottery_results_unlimited = np.zeros((13,13))

    for i in range(nsimulations):
        winners = []
        draws = [odds_draw_one, odds_draw_two, odds_draw_three]
        for draw in draws:
            odds_assignment = []
            for i, j in enumerate(draw):
                odds_assignment += ([ullhp_odds[i]] * int(j * 1000))

            while True:
                draw_winner = random.choice(odds_assignment)
                doprint('draw', draw_winner)
                if draw_winner not in winners:
                    winners.append(draw_winner)
                    break

        doprint('winners', np.array(winners)+1)
        doprint('prelottery', np.array(ullhp_standings)+1)

        draft_order_unlimited = ullhp_standings.copy()
        for winner in winners:
            draft_order_unlimited.remove(winner)
        draft_order_unlimited = winners + draft_order_unlimited

        draft_order_3up = ullhp_standings.copy()
        draft_order_3up_chris = ullhp_standings.copy()
        for i, winner in enumerate(winners[::-1]):
            index_3up = draft_order_3up.index(winner)
            draft_order_3up.remove(winner)

            if index_3up < 3:
                index_3up = 0
            else:
                index_3up -= 3
            draft_order_3up = draft_order_3up[:index_3up] + [winner] + draft_order_3up[index_3up:]

            index_chris = draft_order_3up_chris.index(winner)
            draft_order_3up_chris.remove(winner)
            if index_chris < 3:
                index_chris = 0
            else:
                index_chris -= i + 1
            draft_order_3up_chris = draft_order_3up_chris[:index_chris] + [winner] + draft_order_3up_chris[index_chris:]

        doprint('draft order 3up:', np.array(draft_order_3up) + 1)
        doprint('draft order chris:', np.array(draft_order_3up_chris)+1)
        doprint('draft order unlimited:', np.array(draft_order_unlimited)+1)

        # tabulate results
        for i in ullhp_standings:
            index_3up = draft_order_3up.index(i)
            lottery_results_3up[i][index_3up] += 1

            index_chris = draft_order_3up_chris.index(i)
            lottery_results_chris[i][index_chris] += 1

            index_unlimited = draft_order_unlimited.index(i)
            lottery_results_unlimited[i][index_unlimited] += 1

        doprint('3up/3down', lottery_results_3up)
        doprint('chris', lottery_results_chris)
        doprint('unlimited', lottery_results_unlimited)

    return lottery_results_3up/nsimulations, lottery_results_chris/nsimulations, lottery_results_unlimited/nsimulations


if __name__ == "__main__":

    for teams_in_lotto in range(3,14):

        num_sims = 10000
        r1, r2, r3 = lottery_sim(teams_in_lotto, num_sims)

        # print('3up')
        # print(r1/num_sims)
        # print('3up - chris')
        # print(r2/num_sims)
        # print('Unlimited ')
        # print(r3/num_sims)

        print(teams_in_lotto, r1[0][0], r2[0][0], r3[0][0])
        results = np.hstack([r1,r2,r3])

        np.savetxt(str(teams_in_lotto)+"-lotto.csv", results, delimiter=",")
