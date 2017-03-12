import unittest

from msp430_symex.state import start_path_group

class TestTutorial(unittest.TestCase):
    def test_tutorial(self):
        """
        Test solving the tutorial level of microcorruption.
        """
        dump = \
        "0000:   0000 4400 0000 0000 0000 0000 0000 0000   ..D.............\n" \
        "0010:   *\n" \
        "4400:   3140 0044 1542 5c01 75f3 35d0 085a 3f40   1@.D.B\.u.5..Z?@\n" \
        "4410:   0000 0f93 0724 8245 5c01 2f83 9f4f 8645   .....$.E\./..O.E\n" \
        "4420:   0024 f923 3f40 0000 0f93 0624 8245 5c01   .$.#?@.....$.E\.\n" \
        "4430:   1f83 cf43 0024 fa23 3150 9cff 3f40 a844   ...C.$.#1P..?@.D\n" \
        "4440:   b012 5845 0f41 b012 7a44 0f41 b012 8444   ..XE.A..zD.A...D\n" \
        "4450:   0f93 0520 3f40 c744 b012 5845 063c 3f40   ... ?@.D..XE.<?@\n" \
        "4460:   e444 b012 5845 b012 9c44 0f43 3150 6400   .D..XE...D.C1Pd.\n" \
        "4470:   32d0 f000 fd3f 3040 8445 3e40 6400 b012   2....?0@.E>@d...\n" \
        "4480:   4845 3041 6e4f 1f53 1c53 0e93 fb23 3c90   HE0AnO.S.S...#<.\n" \
        "4490:   0900 0224 0f43 3041 1f43 3041 3012 7f00   ...$.C0A.C0A0.\n" \
        "44a0:   b012 f444 2153 3041 456e 7465 7220 7468   ...D!S0AEnter th\n" \
        "44b0:   6520 7061 7373 776f 7264 2074 6f20 636f   e password to co\n" \
        "44c0:   6e74 696e 7565 0049 6e76 616c 6964 2070   ntinue.Invalid p\n" \
        "44d0:   6173 7377 6f72 643b 2074 7279 2061 6761   assword; try aga\n" \
        "44e0:   696e 2e00 4163 6365 7373 2047 7261 6e74   in..Access Grant\n" \
        "44f0:   6564 2100 1e41 0200 0212 0f4e 8f10 024f   ed!..A.....N...O\n" \
        "4500:   32d0 0080 b012 1000 3241 3041 2183 0f12   2.......2A0A!...\n" \
        "4510:   0312 814f 0400 b012 f444 1f41 0400 3150   ...O.....D.A..1P\n" \
        "4520:   0600 3041 0412 0441 2453 2183 3f40 fcff   ..0A...A$S!.?@..\n" \
        "4530:   0f54 0f12 1312 b012 f444 5f44 fcff 8f11   .T.......D_D....\n" \
        "4540:   3150 0600 3441 3041 0e12 0f12 2312 b012   1P..4A0A....#...\n" \
        "4550:   f444 3150 0600 3041 0b12 0b4f 073c 1b53   .D1P..0A...O.<.S\n" \
        "4560:   8f11 0f12 0312 b012 f444 2152 6f4b 4f93   .........D!RoKO.\n" \
        "4570:   f623 3012 0a00 0312 b012 f444 2152 0f43   .#0........D!R.C\n" \
        "4580:   3b41 3041 0013 0000 0000 0000 0000 0000   ;A0A............\n" \
        "4590:   *\n" \
        "ff80:   7644 7644 7644 7644 7644 7644 7644 7644   vDvDvDvDvDvDvDvD\n" \
        "ff90:   7644 7644 7644 7644 7644 7644 7644 7644   vDvDvDvDvDvDvDvD\n" \
        "ffa0:   7644 7644 7644 7644 7644 7644 7644 7644   vDvDvDvDvDvDvDvD\n" \
        "ffb0:   7644 7644 7644 7644 7644 7644 7644 7644   vDvDvDvDvDvDvDvD\n" \
        "ffc0:   7644 7644 7644 7644 7644 7644 7644 7644   vDvDvDvDvDvDvDvD\n" \
        "ffd0:   7644 7644 7644 7644 7644 7644 7644 7644   vDvDvDvDvDvDvDvD\n" \
        "ffe0:   7644 7644 7644 7644 7644 7644 7644 7644   vDvDvDvDvDvDvDvD\n" \
        "fff0:   7644 7644 7644 7644 7644 7644 7644 0044   vDvDvDvDvDvDvD.D"


        #TODO: automatically find avoid address via CFG
        pg = start_path_group(dump, 0x4400, avoid=0x4454)

        pg.step_until_unlocked()

        unlocked_state = list(pg.unlocked)[0]

        winning_input = unlocked_state.sym_input.dump(unlocked_state).rstrip(b'\xc0')

        self.assertEqual(len(winning_input), 9)
        return winning_input


if __name__ == '__main__':
    unittest.main()
