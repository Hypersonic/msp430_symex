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


class TestNewOrleans(unittest.TestCase):
    def test_new_orleans(self):
        """
        Test solving the New Orleans level of microcorruption.
        """
        dump = \
            "0000:   0000 4400 0000 0000 0000 0000 0000 0000   ..D.............\n" \
            "0010:   *\n" \
            "4400:   3140 0044 1542 5c01 75f3 35d0 085a 3f40   1@.D.B\.u.5..Z?@\n" \
            "4410:   0000 0f93 0724 8245 5c01 2f83 9f4f c245   .....$.E\./..O.E\n" \
            "4420:   0024 f923 3f40 0800 0f93 0624 8245 5c01   .$.#?@.....$.E\.\n" \
            "4430:   1f83 cf43 0024 fa23 3150 9cff b012 7e44   ...C.$.#1P....~D\n" \
            "4440:   3f40 e444 b012 9445 0f41 b012 b244 0f41   ?@.D...E.A...D.A\n" \
            "4450:   b012 bc44 0f93 0520 3f40 0345 b012 9445   ...D... ?@.E...E\n" \
            "4460:   063c 3f40 2045 b012 9445 b012 d644 0f43   .<?@ E...E...D.C\n" \
            "4470:   3150 6400 32d0 f000 fd3f 3040 c045 3f40   1Pd.2....?0@.E?@\n" \
            "4480:   0024 ff40 3300 0000 ff40 4500 0100 ff40   .$.@3....@E....@\n" \
            "4490:   3000 0200 ff40 2300 0300 ff40 2a00 0400   0....@#....@*...\n" \
            "44a0:   ff40 6e00 0500 ff40 7600 0600 cf43 0700   .@n....@v....C..\n" \
            "44b0:   3041 3e40 6400 b012 8445 3041 0e43 0d4f   0A>@d....E0A.C.O\n" \
            "44c0:   0d5e ee9d 0024 0520 1e53 3e92 f823 1f43   .^...$. .S>..#.C\n" \
            "44d0:   3041 0f43 3041 3012 7f00 b012 3045 2153   0A.C0A0...0E!S\n" \
            "44e0:   3041 3041 456e 7465 7220 7468 6520 7061   0A0AEnter the pa\n" \
            "44f0:   7373 776f 7264 2074 6f20 636f 6e74 696e   ssword to contin\n" \
            "4500:   7565 0049 6e76 616c 6964 2070 6173 7377   ue.Invalid passw\n" \
            "4510:   6f72 643b 2074 7279 2061 6761 696e 2e00   ord; try again..\n" \
            "4520:   4163 6365 7373 2047 7261 6e74 6564 2100   Access Granted!.\n" \
            "4530:   1e41 0200 0212 0f4e 8f10 024f 32d0 0080   .A.....N...O2...\n" \
            "4540:   b012 1000 3241 3041 2183 0f12 0312 814f   ....2A0A!......O\n" \
            "4550:   0400 b012 3045 1f41 0400 3150 0600 3041   ....0E.A..1P..0A\n" \
            "4560:   0412 0441 2453 2183 3f40 fcff 0f54 0f12   ...A$S!.?@...T..\n" \
            "4570:   1312 b012 3045 5f44 fcff 8f11 3150 0600   ....0E_D....1P..\n" \
            "4580:   3441 3041 0e12 0f12 2312 b012 3045 3150   4A0A....#...0E1P\n" \
            "4590:   0600 3041 0b12 0b4f 073c 1b53 8f11 0f12   ..0A...O.<.S....\n" \
            "45a0:   0312 b012 3045 2152 6f4b 4f93 f623 3012   ....0E!RoKO..#0.\n" \
            "45b0:   0a00 0312 b012 3045 2152 0f43 3b41 3041   ......0E!R.C;A0A\n" \
            "45c0:   0013 0000 0000 0000 0000 0000 0000 0000   ................\n" \
            "45d0:   *\n" \
            "ff80:   7a44 7a44 7a44 7a44 7a44 7a44 7a44 7a44   zDzDzDzDzDzDzDzD\n" \
            "ff90:   7a44 7a44 7a44 7a44 7a44 7a44 7a44 7a44   zDzDzDzDzDzDzDzD\n" \
            "ffa0:   7a44 7a44 7a44 7a44 7a44 7a44 7a44 7a44   zDzDzDzDzDzDzDzD\n" \
            "ffb0:   7a44 7a44 7a44 7a44 7a44 7a44 7a44 7a44   zDzDzDzDzDzDzDzD\n" \
            "ffc0:   7a44 7a44 7a44 7a44 7a44 7a44 7a44 7a44   zDzDzDzDzDzDzDzD\n" \
            "ffd0:   7a44 7a44 7a44 7a44 7a44 7a44 7a44 7a44   zDzDzDzDzDzDzDzD\n" \
            "ffe0:   7a44 7a44 7a44 7a44 7a44 7a44 7a44 7a44   zDzDzDzDzDzDzDzD\n" \
            "fff0:   7a44 7a44 7a44 7a44 7a44 7a44 7a44 0044   zDzDzDzDzDzDzD.D"

        #TODO: automatically find avoid address via CFG
        pg = start_path_group(dump, 0x4400, avoid=0x4458)

        pg.step_until_unlocked()

        unlocked_state = list(pg.unlocked)[0]

        winning_input = unlocked_state.sym_input.dump(unlocked_state).rstrip(b'\xc0')

        self.assertEqual(winning_input, b'3E0#*nv\x00')


class TestSydney(unittest.TestCase):
    def test_sydney(self):
        """
        Test solving the Sydney level of microcorruption.
        """
        dump = \
            "0000:   0000 4400 0000 0000 0000 0000 0000 0000   ..D.............\n" \
            "0010:   *\n" \
            "4400:   3140 0044 1542 5c01 75f3 35d0 085a 3f40   1@.D.B\.u.5..Z?@\n" \
            "4410:   0000 0f93 0724 8245 5c01 2f83 9f4f 9445   .....$.E\./..O.E\n" \
            "4420:   0024 f923 3f40 0000 0f93 0624 8245 5c01   .$.#?@.....$.E\.\n" \
            "4430:   1f83 cf43 0024 fa23 3150 9cff 3f40 b444   ...C.$.#1P..?@.D\n" \
            "4440:   b012 6645 0f41 b012 8044 0f41 b012 8a44   ..fE.A...D.A...D\n" \
            "4450:   0f93 0520 3f40 d444 b012 6645 093c 3f40   ... ?@.D..fE.<?@\n" \
            "4460:   f144 b012 6645 3012 7f00 b012 0245 2153   .D..fE0....E!S\n" \
            "4470:   0f43 3150 6400 32d0 f000 fd3f 3040 9245   .C1Pd.2....?0@.E\n" \
            "4480:   3e40 6400 b012 5645 3041 bf90 2555 0000   >@d...VE0A..%U..\n" \
            "4490:   0d20 bf90 402b 0200 0920 bf90 4450 0400   . ..@+... ..DP..\n" \
            "44a0:   0520 1e43 bf90 6f27 0600 0124 0e43 0f4e   . .C..o'...$.C.N\n" \
            "44b0:   3041 3041 456e 7465 7220 7468 6520 7061   0A0AEnter the pa\n" \
            "44c0:   7373 776f 7264 2074 6f20 636f 6e74 696e   ssword to contin\n" \
            "44d0:   7565 2e00 496e 7661 6c69 6420 7061 7373   ue..Invalid pass\n" \
            "44e0:   776f 7264 3b20 7472 7920 6167 6169 6e2e   word; try again.\n" \
            "44f0:   0041 6363 6573 7320 4772 616e 7465 6421   .Access Granted!\n" \
            "4500:   0000 1e41 0200 0212 0f4e 8f10 024f 32d0   ...A.....N...O2.\n" \
            "4510:   0080 b012 1000 3241 3041 2183 0f12 0312   ......2A0A!.....\n" \
            "4520:   814f 0400 b012 0245 1f41 0400 3150 0600   .O.....E.A..1P..\n" \
            "4530:   3041 0412 0441 2453 2183 3f40 fcff 0f54   0A...A$S!.?@...T\n" \
            "4540:   0f12 1312 b012 0245 5f44 fcff 8f11 3150   .......E_D....1P\n" \
            "4550:   0600 3441 3041 0e12 0f12 2312 b012 0245   ..4A0A....#....E\n" \
            "4560:   3150 0600 3041 0b12 0b4f 073c 1b53 8f11   1P..0A...O.<.S..\n" \
            "4570:   0f12 0312 b012 0245 2152 6f4b 4f93 f623   .......E!RoKO..#\n" \
            "4580:   3012 0a00 0312 b012 0245 2152 0f43 3b41   0........E!R.C;A\n" \
            "4590:   3041 0013 0000 0000 0000 0000 0000 0000   0A..............\n" \
            "45a0:   *\n" \
            "ff80:   7c44 7c44 7c44 7c44 7c44 7c44 7c44 7c44   |D|D|D|D|D|D|D|D\n" \
            "ff90:   7c44 7c44 7c44 7c44 7c44 7c44 7c44 7c44   |D|D|D|D|D|D|D|D\n" \
            "ffa0:   7c44 7c44 7c44 7c44 7c44 7c44 7c44 7c44   |D|D|D|D|D|D|D|D\n" \
            "ffb0:   7c44 7c44 7c44 7c44 7c44 7c44 7c44 7c44   |D|D|D|D|D|D|D|D\n" \
            "ffc0:   7c44 7c44 7c44 7c44 7c44 7c44 7c44 7c44   |D|D|D|D|D|D|D|D\n" \
            "ffd0:   7c44 7c44 7c44 7c44 7c44 7c44 7c44 7c44   |D|D|D|D|D|D|D|D\n" \
            "ffe0:   7c44 7c44 7c44 7c44 7c44 7c44 7c44 7c44   |D|D|D|D|D|D|D|D\n" \
            "fff0:   7c44 7c44 7c44 7c44 7c44 7c44 7c44 0044   |D|D|D|D|D|D|D.D"


        #TODO: automatically find avoid address via CFG
        pg = start_path_group(dump, 0x4400, avoid=0x4454)

        pg.step_until_unlocked()

        unlocked_state = list(pg.unlocked)[0]

        winning_input = unlocked_state.sym_input.dump(unlocked_state).rstrip(b'\xc0')

        self.assertEqual(winning_input, b"%U@+DPo'")


class TestHanoi(unittest.TestCase):
    
    def test_hanoi(self):
        dump = \
            """0000:   0000 4400 0000 0000 0000 0000 0000 0000   ..D.............
0010:   *
4400:   3140 0044 1542 5c01 75f3 35d0 085a 3f40   1@.D.B\.u.5..Z?@
4410:   0000 0f93 0724 8245 5c01 2f83 9f4f 0c46   .....$.E\./..O.F
4420:   0024 f923 3f40 2200 0f93 0624 8245 5c01   .$.#?@"....$.E\.
4430:   1f83 cf43 0024 fa23 b012 2045 0f43 32d0   ...C.$.#.. E.C2.
4440:   f000 fd3f 3040 0a46 3012 7f00 b012 7a45   ...?0@.F0...zE
4450:   2153 3041 0412 0441 2453 2183 c443 fcff   !S0A...A$S!..C..
4460:   3e40 fcff 0e54 0e12 0f12 3012 7d00 b012   >@...T....0.}...
4470:   7a45 5f44 fcff 8f11 3152 3441 3041 456e   zE_D....1R4A0AEn
4480:   7465 7220 7468 6520 7061 7373 776f 7264   ter the password
4490:   2074 6f20 636f 6e74 696e 7565 2e00 5265    to continue..Re
44a0:   6d65 6d62 6572 3a20 7061 7373 776f 7264   member: password
44b0:   7320 6172 6520 6265 7477 6565 6e20 3820   s are between 8 
44c0:   616e 6420 3136 2063 6861 7261 6374 6572   and 16 character
44d0:   732e 0054 6573 7469 6e67 2069 6620 7061   s..Testing if pa
44e0:   7373 776f 7264 2069 7320 7661 6c69 642e   ssword is valid.
44f0:   0041 6363 6573 7320 6772 616e 7465 642e   .Access granted.
4500:   0054 6861 7420 7061 7373 776f 7264 2069   .That password i
4510:   7320 6e6f 7420 636f 7272 6563 742e 0000   s not correct...
4520:   c243 1024 3f40 7e44 b012 de45 3f40 9e44   .C.$?@~D...E?@.D
4530:   b012 de45 3e40 1c00 3f40 0024 b012 ce45   ...E>@..?@.$...E
4540:   3f40 0024 b012 5444 0f93 0324 f240 a700   ?@.$..TD...$.@..
4550:   1024 3f40 d344 b012 de45 f290 3400 1024   .$?@.D...E..4..$
4560:   0720 3f40 f144 b012 de45 b012 4844 3041   . ?@.D...E..HD0A
4570:   3f40 0145 b012 de45 3041 1e41 0200 0212   ?@.E...E0A.A....
4580:   0f4e 8f10 024f 32d0 0080 b012 1000 3241   .N...O2.......2A
4590:   3041 2183 0f12 0312 814f 0400 b012 7a45   0A!......O....zE
45a0:   1f41 0400 3150 0600 3041 0412 0441 2453   .A..1P..0A...A$S
45b0:   2183 3f40 fcff 0f54 0f12 1312 b012 7a45   !.?@...T......zE
45c0:   5f44 fcff 8f11 3150 0600 3441 3041 0e12   _D....1P..4A0A..
45d0:   0f12 2312 b012 7a45 3150 0600 3041 0b12   ..#...zE1P..0A..
45e0:   0b4f 073c 1b53 8f11 0f12 0312 b012 7a45   .O.<.S........zE
45f0:   2152 6f4b 4f93 f623 3012 0a00 0312 b012   !RoKO..#0.......
4600:   7a45 2152 0f43 3b41 3041 0013 0000 0000   zE!R.C;A0A......
4610:   *
ff80:   4444 4444 4444 4444 4444 4444 4444 4444   DDDDDDDDDDDDDDDD
ff90:   4444 4444 4444 4444 4444 4444 4444 4444   DDDDDDDDDDDDDDDD
ffa0:   4444 4444 4444 4444 4444 4444 4444 4444   DDDDDDDDDDDDDDDD
ffb0:   4444 4444 4444 4444 4444 4444 4444 4444   DDDDDDDDDDDDDDDD
ffc0:   4444 4444 4444 4444 4444 4444 4444 4444   DDDDDDDDDDDDDDDD
ffd0:   4444 4444 4444 4444 4444 4444 4444 4444   DDDDDDDDDDDDDDDD
ffe0:   4444 4444 4444 4444 4444 4444 4444 4444   DDDDDDDDDDDDDDDD
fff0:   4444 4444 4444 4444 4444 4444 4444 0044   DDDDDDDDDDDDDD.D"""

        #TODO: automatically find avoid address via CFG
        pg = start_path_group(dump, 0x4400, avoid=0x4570)

        pg.step_until_unlocked()

        unlocked_state = list(pg.unlocked)[0]

        winning_input = unlocked_state.sym_input.dump(unlocked_state).rstrip(b'\xc0')

        # b'AAAAAAAAAAAAAAAA4' ('A's can be anything)
        self.assertEqual(len(winning_input), 17)
        self.assertEqual(winning_input[16], b'4') # overflow with correct value

if __name__ == '__main__':
    unittest.main()
