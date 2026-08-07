######################################################################################
# music.py       Version 5.0     22-Jun-2026
#
# Taj Ballinger, Trevor Ritchie, Drew Smuniewski, and Bill Manaris
#
#######################################################################################
#
# This file is part of PythonMusic.
#
# PythonMusic is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# PythonMusic is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with PythonMusic.  If not, see <https://www.gnu.org/licenses/>.
#
# PythonMusic derives from JythonMusic (https://jythonmusic.me),
# Copyright (C) 2011-2023 Bill Manaris, John-Anthony Thevos, Marge Marshall,
# Chris Benson, and Kenneth Hanson.
# Modifications Copyright (C) 2025 Dr. Bill Manaris and the PythonMusic contributors.
#
#######################################################################################
#
# REVISIONS:
#
# 5.0   22-Jun-2026 (tb)   Ported from JythonMusic to PythonMusic.
#      - Replaced jMusic/jSyn backend
#         - MIDI synthesis is handled by tinysoundfont
#         - AudioSample now uses realtime sounddevice engine (RealtimeAudioPlayer)
#      - Natively implemented removed jMusic/jSyn structures:
#         - Fully implemented Note/Phrase/Part/Score
#         - Defined musical constants
#         - Read/Write now use mido for MIDI files, was jMusic I/O
#         - Ported and completed View using Verovio/matplotlib/pypianoroll
#      - Added full Google-style docstrings throughout
#
#######################################################################################

import PythonMusic                      # preloads the bundled portaudio binary on macOS (must precede tinysoundfont/pyaudio)
from utilities import *    # mapValue, etc.
import numpy as np                     # mathematical operations like frequency calculations
from timer import Timer, LinearRamp    # scheduling audio events and playback timing
import weakref                         # weak references for timer tracking
import time                            # timestamps and sleep operations
import atexit                          # registering cleanup functions to run on program exit
import tinysoundfont                   # MIDI synthesis

######################################################################################
# define scales as lists of pitch offsets (from the root)
AEOLIAN_SCALE        = [0, 2, 3, 5, 7, 8, 10]
BLUES_SCALE          = [0, 2, 3, 4, 5, 7, 9, 10, 11]
CHROMATIC_SCALE      = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
DIATONIC_MINOR_SCALE = [0, 2, 3, 5, 7, 8, 10]
DORIAN_SCALE         = [0, 2, 3, 5, 7, 9, 10]
HARMONIC_MINOR_SCALE = [0, 2, 3, 5, 7, 8, 11]
LYDIAN_SCALE         = [0, 2, 4, 6, 7, 9, 11]
MAJOR_SCALE          = [0, 2, 4, 5, 7, 9, 11]
MELODIC_MINOR_SCALE  = [0, 2, 3, 5, 7, 8, 9, 10, 11]
MINOR_SCALE          = [0, 2, 3, 5, 7, 8, 10]
MIXOLYDIAN_SCALE     = [0, 2, 4, 5, 7, 9, 10]
NATURAL_MINOR_SCALE  = [0, 2, 3, 5, 7, 8, 10]
PENTATONIC_SCALE     = [0, 2, 4, 7, 9]

######################################################################################
# define text labels for MIDI instruments (index in list is same as MIDI instrument number)
MIDI_INSTRUMENTS = [ # Piano Family
                    "Acoustic Grand Piano", "Bright Acoustic Piano", "Electric Grand Piano",
                    "Honky-tonk Piano", "Electric Piano 1 (Rhodes)", "Electric Piano 2 (DX)",
                    "Harpsichord", "Clavinet",

                    # Chromatic Percussion Family
                    "Celesta", "Glockenspiel", "Music Box", "Vibraphone", "Marimba",
                    "Xylophone", "Tubular Bells", "Dulcimer",

                    # Organ Family
                    "Drawbar Organ", "Percussive Organ", "Rock Organ", "Church Organ",
                    "Reed Organ", "Accordion", "Harmonica", "Tango Accordion",

                    # Guitar Family
                    "Acoustic Guitar (nylon)", "Acoustic Guitar (steel)", "Electric Guitar (jazz)",
                    "Electric Guitar (clean)", "Electric Guitar (muted)", "Overdriven Guitar",
                    "Distortion Guitar", "Guitar harmonics",

                    # Bass Family
                    "Acoustic Bass", "Electric Bass (finger)", "Electric Bass (pick)", "Fretless Bass",
                    "Slap Bass 1", "Slap Bass 2", "Synth Bass 1", "Synth Bass 2",

                    # Strings and Timpani Family
                    "Violin", "Viola", "Cello", "Contrabass", "Tremolo Strings", "Pizzicato Strings",
                    "Orchestral Harp", "Timpani",

                    # Ensemble Family
                    "String Ensemble 1", "String Ensemble 2", "Synth Strings 1", "Synth Strings 2",
                    "Choir Aahs", "Voice Oohs", "Synth Voice", "Orchestra Hit",

                    # Brass Family
                    "Trumpet", "Trombone", "Tuba", "Muted Trumpet", "French Horn",
                    "Brass Section", "SynthBrass 1", "SynthBrass 2",

                    # Reed Family
                    "Soprano Sax", "Alto Sax", "Tenor Sax", "Baritone Sax", "Oboe", "English Horn",
                    "Bassoon", "Clarinet",

                    # Pipe Family
                    "Piccolo", "Flute", "Recorder", "Pan Flute", "Blown Bottle", "Shakuhachi",
                    "Whistle", "Ocarina",

                    # Synth Lead Family
                    "Lead 1 (square)", "Lead 2 (sawtooth)", "Lead 3 (calliope)",  "Lead 4 (chiff)",
                    "Lead 5 (charang)", "Lead 6 (voice)", "Lead 7 (fifths)", "Lead 8 (bass + lead)",

                    # Synth Pad Family
                    "Pad 1 (new age)", "Pad 2 (warm)", "Pad 3 (polysynth)", "Pad 4 (choir)",
                    "Pad 5 (bowed)", "Pad 6 (metallic)", "Pad 7 (halo)", "Pad 8 (sweep)",

                    # Synth Effects Family
                    "FX 1 (rain)", "FX 2 (soundtrack)", "FX 3 (crystal)", "FX 4 (atmosphere)",
                    "FX 5 (brightness)", "FX 6 (goblins)", "FX 7 (echoes)", "FX 8 (sci-fi)",

                    # Ethnic Family
                    "Sitar",  "Banjo", "Shamisen", "Koto", "Kalimba", "Bag pipe", "Fiddle", "Shanai",

                    # Percussive Family
                    "Tinkle Bell", "Agogo", "Steel Drums", "Woodblock", "Taiko Drum", "Melodic Tom",
                    "Synth Drum", "Reverse Cymbal",

                    # Sound Effects Family
                    "Guitar Fret Noise", "Breath Noise", "Seashore", "Bird Tweet", "Telephone Ring",
                    "Helicopter", "Applause", "Gunshot" ]

# define text labels for inverse-lookup of MIDI pitches (index in list is same as MIDI pitch number)
# (for enharmonic notes, e.g., FS4 and GF4, uses the sharp version, e.g. FS4)
MIDI_PITCHES = ["C_1", "CS_1", "D_1", "DS_1", "E_1", "F_1", "FS_1", "G_1", "GS_1", "A_1", "AS_1", "B_1",
                "C0", "CS0", "D0", "DS0", "E0", "F0", "FS0", "G0", "GS0", "A0", "AS0", "B0",
                "C1", "CS1", "D1", "DS1", "E1", "F1", "FS1", "G1", "GS1", "A1", "AS1", "B1",
                "C2", "CS2", "D2", "DS2", "E2", "F2", "FS2", "G2", "GS2", "A2", "AS2", "B2",
                "C3", "CS3", "D3", "DS3", "E3", "F3", "FS3", "G3", "GS3", "A3", "AS3", "B3",
                "C4", "CS4", "D4", "DS4", "E4", "F4", "FS4", "G4", "GS4", "A4", "AS4", "B4",
                "C5", "CS5", "D5", "DS5", "E5", "F5", "FS5", "G5", "GS5", "A5", "AS5", "B5",
                "C6", "CS6", "D6", "DS6", "E6", "F6", "FS6", "G6", "GS6", "A6", "AS6", "B6",
                "C7", "CS7", "D7", "DS7", "E7", "F7", "FS7", "G7", "GS7", "A7", "AS7", "B7",
                "C8", "CS8", "D8", "DS8", "E8", "F8", "FS8", "G8", "GS8", "A8", "AS8", "B8",
                "C9", "CS9", "D9", "DS9", "E9", "F9", "FS9", "G9"]

#######################################################################################
# MIDI rhythm/duration constants

DWN  = DOTTED_WHOLE_NOTE          = 6.0
WN   = WHOLE_NOTE                 = 4.0
DHN  = DOTTED_HALF_NOTE           = 3.0
DDHN = DOUBLE_DOTTED_HALF_NOTE    = 3.5
HN   = HALF_NOTE                  = 2.0
HNT  = HALF_NOTE_TRIPLET          = 4.0/3.0
QN   = QUARTER_NOTE               = 1.0
QNT  = QUARTER_NOTE_TRIPLET       = 2.0/3.0
DQN  = DOTTED_QUARTER_NOTE        = 1.5
DDQN = DOUBLE_DOTTED_QUARTER_NOTE = 1.75
EN   = EIGHTH_NOTE                = 0.5
DEN  = DOTTED_EIGHTH_NOTE         = 0.75
ENT  = EIGHTH_NOTE_TRIPLET        = 1.0/3.0
DDEN = DOUBLE_DOTTED_EIGHTH_NOTE  = 0.875
SN   = SIXTEENTH_NOTE             = 0.25
DSN  = DOTTED_SIXTEENTH_NOTE      = 0.375
SNT  = SIXTEENTH_NOTE_TRIPLET     = 1.0/6.0
TN   = THIRTYSECOND_NOTE          = 0.125
TNT  = THIRTYSECOND_NOTE_TRIPLET  = 1.0/12.0

REST = -2147483648
DEFAULT_LENGTH_MULTIPLIER = 0.9

######################################################################################
# MIDI pitch constants (for first octave, i.e., minus 1 octave)
C_1  = c_1                = 0
CS_1 = cs_1 = DF_1 = df_1 = 1
D_1  = d_1                = 2
EF_1 = ef_1 = DS_1 = ds_1 = 3
E_1  = e_1  = FF_1 = ff_1 = 4
F_1  = f_1  = ES_1 = es_1 = 5
FS_1 = fs_1 = GF_1 = gf_1 = 6
G_1  = g_1                = 7
AF_1 = af_1 = GS_1 = gs_1 = 8
A_1  = a_1                = 9
BF_1 = bf_1 = AS_1 = as_1 = 10
B_1  = b_1  = CF0  = cf0  = 11
C0   = c0   = BS_1 = bs_1 = 12
CS0  = cs0  = DF0  = df0  = 13
D0   = d0                 = 14
EF0  = ef0  = DS0  = ds0  = 15
E0   = e0   = FF0  = ff0  = 16
F0   = f0   = ES0  = es0  = 17
FS0  = fs0  = GF0  = gf0  = 18
G0   = g0                 = 19
AF0  = af0  = GS0  = gs0  = 20
A0   = a0                 = 21
BF0  = bf0  = AS0  = as0  = 22
B0   = b0   = CF1  = cf1  = 23
C1   = c1   = BS0  = bs0  = 24
CS1  = cs1  = DF1  = df1  = 25
D1   = d1                 = 26
EF1  = ef1  = DS1  = ds1  = 27
E1   = e1   = FF1  = ff1  = 28
F1   = f1   = ES1  = es1  = 29
FS1  = fs1  = GF1  = gf1  = 30
G1   = g1                 = 31
AF1  = af1  = GS1  = gs1  = 32
A1   = a1                 = 33
BF1  = bf1  = AS1  = as1  = 34
B1   = b1   = CF2  = cf2  = 35
C2   = c2   = BS1  = bs1  = 36
CS2  = cs2  = DF2  = df2  = 37
D2   = d2                 = 38
EF2  = ef2  = DS2  = ds2  = 39
E2   = e2   = FF2  = ff2  = 40
F2   = f2   = ES2  = es2  = 41
FS2  = fs2  = GF2  = gf2  = 42
G2   = g2                 = 43
AF2  = af2  = GS2  = gs2  = 44
A2   = a2                 = 45
BF2  = bf2  = AS2  = as2  = 46
B2   = b2   = CF3  = cf3  = 47
C3   = c3   = BS2  = bs2  = 48
CS3  = cs3  = DF3  = df3  = 49
D3   = d3                 = 50
EF3  = ef3  = DS3  = ds3  = 51
E3   = e3   = FF3  = ff3  = 52
F3   = f3   = ES3  = es3  = 53
FS3  = fs3  = GF3  = gf3  = 54
G3   = g3                 = 55
AF3  = af3  = GS3  = gs3  = 56
A3   = a3                 = 57
BF3  = bf3  = AS3  = as3  = 58
B3   = b3   = CF4  = cf4  = 59
C4   = c4   = BS3  = bs3  = 60
CS4  = cs4  = DF4  = df4  = 61
D4   = d4                 = 62
EF4  = ef4  = DS4  = ds4  = 63
E4   = e4   = FF4  = ff4  = 64
F4   = f4   = ES4  = es4  = 65
FS4  = fs4  = GF4  = gf4  = 66
G4   = g4                 = 67
AF4  = af4  = GS4  = gs4  = 68
A4   = a4                 = 69
BF4  = bf4  = AS4  = as4  = 70
B4   = b4   = CF5  = cf5  = 71
C5   = c5   = BS4  = bs4  = 72
CS5  = cs5  = DF5  = df5  = 73
D5   = d5                 = 74
EF5  = ef5  = DS5  = ds5  = 75
E5   = e5   = FF5  = ff5  = 76
F5   = f5   = ES5  = es5  = 77
FS5  = fs5  = GF5  = gf5  = 78
G5   = g5                 = 79
AF5  = af5  = GS5  = gs5  = 80
A5   = a5                 = 81
BF5  = bf5  = AS5  = as5  = 82
B5   = b5   = CF6  = cf6  = 83
C6   = c6   = BS5  = bs5  = 84
CS6  = cs6  = DF6  = df6  = 85
D6   = d6                 = 86
EF6  = ef6  = DS6  = ds6  = 87
E6   = e6   = FF6  = ff6  = 88
F6   = f6   = ES6  = es6  = 89
FS6  = fs6  = GF6  = gf6  = 90
G6   = g6                 = 91
AF6  = af6  = GS6  = gs6  = 92
A6   = a6                 = 93
BF6  = bf6  = AS6  = as6  = 94
B6   = b6   = CF7  = cf7  = 95
C7   = c7   = BS6  = bs6  = 96
CS7  = cs7  = DF7  = df7  = 97
D7   = d7                 = 98
EF7  = ef7  = DS7  = ds7  = 99
E7   = e7   = FF7  = ff7  = 100
F7   = f7   = ES7  = es7  = 101
FS7  = fs7  = GF7  = gf7  = 102
G7   = g7                 = 103
AF7  = af7  = GS7  = gs7  = 104
A7   = a7                 = 105
BF7  = bf7  = AS7  = as7  = 106
B7   = b7   = CF8  = cf8  = 107
C8   = c8   = BS7  = bs7  = 108
CS8  = cs8  = DF8  = df8  = 109
D8   = d8                 = 110
EF8  = ef8  = DS8  = ds8  = 111
E8   = e8   = FF8  = ff8  = 112
F8   = f8   = ES8  = es8  = 113
FS8  = fs8  = GF8  = gf8  = 114
G8   = g8                 = 115
AF8  = af8  = GS8  = gs8  = 116
A8   = a8                 = 117
BF8  = bf8  = AS8  = as8  = 118
B8   = b8   = CF9  = cf9  = 119
C9   = c9   = BS8  = bs8  = 120
CS9  = cs9  = DF9  = df9  = 121
D9   = d9                 = 122
EF9  = ef9  = DS9  = ds9  = 123
E9   = e9   = FF9  = ff9  = 124
F9   = f9   = ES9  = es9  = 125
FS9  = fs9  = GF9  = gf9  = 126
G9   = g9                 = 127

######################################################################################
# MIDI instrument constants
ACOUSTIC_GRAND = PIANO = 0
BRIGHT_ACOUSTIC = 1
ELECTRIC_GRAND = 2
HONKYTONK_PIANO = HONKYTONK = 3
EPIANO = EPIANO1 = RHODES_PIANO = RHODES = 4
EPIANO2 = DX_PIANO = DX = 5
HARPSICHORD = 6
CLAVINET = 7
CELESTA = 8
GLOCKENSPIEL = 9
MUSIC_BOX = 10
VIBRAPHONE = VIBES = 11
MARIMBA = 12
XYLOPHONE = 13
BELLS = TUBULAR_BELLS = 14
DULCIMER = 15
DRAWBAR_ORGAN = ORGAN = 16
PERCUSSIVE_ORGAN = JAZZ_ORGAN = 17
ROCK_ORGAN = 18
CHURCH_ORGAN = 19
REED_ORGAN = 20
ACCORDION = 21
HARMONICA = 22
TANGO_ACCORDION = BANDONEON = 23
NYLON_GUITAR = GUITAR = 24
STEEL_GUITAR = 25
JAZZ_GUITAR = 26
CLEAN_GUITAR = ELECTRIC_GUITAR = 27
MUTED_GUITAR = 28
OVERDRIVE_GUITAR = OVERDRIVEN_GUITAR = 29
DISTORTION_GUITAR = 30
GUITAR_HARMONICS = 31
ACOUSTIC_BASS = 32
BASS = ELECTRIC_BASS = FINGERED_BASS = 33
PICKED_BASS = 34
FRETLESS_BASS = 35
SLAP_BASS1 = 36
SLAP_BASS2 = 37
SYNTH_BASS1 = 38
SYNTH_BASS2 = 39
VIOLIN = 40
VIOLA = 41
CELLO = 42
CONTRABASS = 43
TREMOLO_STRINGS = 44
PIZZICATO_STRINGS = 45
ORCHESTRAL_HARP = HARP = 46
TIMPANI = 47
STRING_ENSEMBLE1 = STRINGS = 48
STRING_ENSEMBLE2 = 49
SYNTH_STRINGS1 = SYNTH = 50
SYNTH_STRINGS2 = 51
CHOIR_AHHS = CHOIR = 52
VOICE_OOHS = VOICE = 53
SYNTH_VOICE = VOX = 54
ORCHESTRA_HIT = 55
TRUMPET = 56
TROMBONE = 57
TUBA = 58
MUTED_TRUMPET = 59
FRENCH_HORN = HORN = 60
BRASS_SECTION = BRASS = 61
SYNTH_BRASS1 = 62
SYNTH_BRASS2 = 63
SOPRANO_SAX = SOPRANO_SAXOPHONE = 64
ALTO_SAX = ALTO_SAXOPHONE = 65
TENOR_SAX = TENOR_SAXOPHONE = SAX = SAXOPHONE = 66
BARITONE_SAX = BARITONE_SAXOPHONE = 67
OBOE = 68
ENGLISH_HORN = 69
BASSOON = 70
CLARINET = 71
PICCOLO = 72
FLUTE = 73
RECORDER = 74
PAN_FLUTE = 75
BLOWN_BOTTLE = BOTTLE = 76
SHAKUHACHI = 77
WHISTLE = 78
OCARINA = 79
LEAD_1_SQUARE = SQUARE = 80
LEAD_2_SAWTOOTH = SAWTOOTH = 81
LEAD_3_CALLIOPE = CALLIOPE = 82
LEAD_4_CHIFF = CHIFF = 83
LEAD_5_CHARANG = CHARANG = 84
LEAD_6_VOICE = SOLO_VOX = 85
LEAD_7_FIFTHS = FIFTHS = 86
LEAD_8_BASS_LEAD = BASS_LEAD = 87
PAD_1_NEW_AGE = NEW_AGE = 88
PAD_2_WARM = WARM_PAD = 89
PAD_3_POLYSYNTH = POLYSYNTH = 90
PAD_4_CHOIR = SPACE_VOICE = 91
PAD_5_GLASS = BOWED_GLASS = 92
PAD_6_METTALIC = METALLIC = 93
PAD_7_HALO = 94
PAD_8_SWEEP = 95
FX_1_RAIN = ICE_RAIN = 96
FX_2_SOUNDTRACK = 97
FX_3_CRYSTAL = 98
FX_4_ATMOSPHERE = 99
FX_5_BRIGHTNESS = BRIGHTNESS = 100
FX_6_GOBLINS = GOBLINS = 101
FX_7_ECHOES = ECHO_DROPS = 102
FX_8_SCI_FI = SCI_FI = 103
SITAR = 104
BANJO = 105
SHAMISEN = 106
KOTO = 107
KALIMBA = 108
BAGPIPE = 109
FIDDLE = 110
SHANNAI = 111
TINKLE_BELL = BELL = 112
AGOGO = 113
STEEL_DRUMS = 114
WOODBLOCK = 115
TAIKO_DRUM = TAIKO = 116
MELODIC_TOM = TOM_TOM = 117
SYNTH_DRUM = 118
REVERSE_CYMBAL = 119
GUITAR_FRET_NOISE = FRET_NOISE = 120
BREATH_NOISE = BREATHNOISE = BREATH = 121
SEASHORE = SEA = 122
BIRD_TWEET = BIRD = 123
TELEPHONE_RING = TELEPHONE = 124
HELICOPTER = 125
APPLAUSE = 126
GUNSHOT = 127

# and MIDI drum constants
ABD = ACOUSTIC_BASS_DRUM = 35
BDR = BASS_DRUM = 36
STK = SIDE_STICK = 37
SNR = SNARE = 38
CLP = HAND_CLAP = 39
ESN = ELECTRIC_SNARE = 40
LFT = LOW_FLOOR_TOM = 41
CHH = CLOSED_HI_HAT = 42
HFT = HIGH_FLOOR_TOM = 43
PHH = PEDAL_HI_HAT = 44
LTM = LOW_TOM = 45
OHH = OPEN_HI_HAT = 46
LMT = LOW_MID_TOM = 47
HMT = HI_MID_TOM = 48
CC1 = CRASH_CYMBAL_1 = 49
HGT = HIGH_TOM = 50
RC1 = RIDE_CYMBAL_1 = 51
CCM = CHINESE_CYMBAL = 52
RBL = RIDE_BELL = 53
TMB = TAMBOURINE = 54
SCM = SPLASH_CYMBAL = 55
CBL = COWBELL = 56
CC2 = CRASH_CYMBAL_2 = 57
VSP = VIBRASLAP = 58
RC2 = RIDE_CYMBAL_2 = 59
HBG = HI_BONGO = 60
LBG = LOW_BONGO = 61
MHC = MUTE_HI_CONGA = 62
OHC = OPEN_HI_CONGA = 63
LCG = LOW_CONGA = 64
HTI = HIGH_TIMBALE = 65
LTI = LOW_TIMBALE = 66
HAG = HIGH_AGOGO = 67
LAG = LOW_AGOGO = 68
CBS = CABASA = 69
MRC = MARACAS = 70
SWH = SHORT_WHISTLE = 71
LWH = LONG_WHISTLE = 72
SGU = SHORT_GUIRO = 73
LGU = LONG_GUIRO = 74
CLA = CLAVES = 75
HWB = HI_WOOD_BLOCK = 76
LWB = LOW_WOOD_BLOCK = 77
MCU = MUTE_CUICA = 78
OCU = OPEN_CUICA = 79
MTR = MUTE_TRIANGLE = 80
OTR = OPEN_TRIANGLE = 81

######################################################################################
# dynamics, panning, and pitch bend
FFF = 120
FORTISSIMO = FF = 100
FORTE = F = 85
MEZZO_FORTE = MF = 70
MEZZO_PIANO = MP = 60
P = 50   # avoid conflict with piano instrument
PIANISSIMO = PP = 25
PPP = 10
SILENT = 0

PAN_LEFT = 0.0
PAN_CENTER = 0.5
PAN_RIGHT = 1.0

# The MIDI specification is that pitch bend is a 14-bit value, where zero is
# maximum downward bend, 16383 is maximum upward bend, and 8192 is the center (no pitch bend).
MIDI_PITCHBEND_MIN    = 0
MIDI_PITCHBEND_MAX    = 16383
MIDI_PITCHBEND_NORMAL = 8192

# how we represent pitch bend in our API (-8192 to 8192)
OUR_PITCHBEND_MIN    = -MIDI_PITCHBEND_NORMAL
OUR_PITCHBEND_MAX    = MIDI_PITCHBEND_MAX - MIDI_PITCHBEND_NORMAL
OUR_PITCHBEND_NORMAL = MIDI_PITCHBEND_MIN

# initialize pitchbend across channels to 0
_currentPitchbend = {}    # holds pitchbend to be used when playing a note / frequency (see below)
for i in range(16):
   _currentPitchbend[i] = OUR_PITCHBEND_NORMAL   # set this channel's pitchbend to zero

#######################################################################################
# Note <-> Frequency Conversion
#######################################################################################

def frequencyToPitch(frequency):
   """Convert a frequency to the nearest MIDI pitch plus a pitch bend.

   The pitch bend captures the leftover distance to the exact frequency, for finer
   control. A4 (concert pitch, 440 Hz) is pitch 69.

   Args:
       frequency (float): The frequency to convert, in hertz (8.17 to 12600.0).

   Returns:
       pitch (int): The nearest MIDI pitch, from 0 to 127.
       pitchBend (int): The leftover bend to the exact frequency, in pitch bend units from -8191 to 8192, where 0 means no bend.
   """
   concertPitch = 440.0   # 440Hz
   bendRange = 4          # 4 semitones (2 below, 2 above)

   x = np.log2(frequency / concertPitch) * 12 + 69
   pitch = int(round(x))
   pitchBend = int(round((x - pitch) * 8192 / bendRange * 2))

   return pitch, pitchBend

# create alias
freqToNote = frequencyToPitch


def pitchToFrequency(pitch):
   """Convert a MIDI pitch to its frequency.

   A4 (pitch 69) is concert pitch, 440 Hz.

   Args:
       pitch (int or float): The MIDI pitch to convert, from 0 to 127.

   Returns:
       frequency (float): The matching frequency, in hertz (8.17 to 12600.0).
   """
   concertPitch = 440.0   # 440Hz

   frequency = concertPitch * 2 ** ( (pitch - 69) / 12.0 )

   return frequency

# create alias
noteToFreq = pitchToFrequency


#######################################################################################
#### Transciption Classes #############################################################
#######################################################################################

class Note():
   """Represent a single note: a pitch, how long it lasts, and how it is played.

   The pitch can be a MIDI pitch or a frequency in hertz (8.17 to 12600.0). Pass REST for the value to
   make a silent note (a rest).

   Args:
       value (int or float): A MIDI pitch from 0 to 127, or a frequency in hertz (8.17 to 12600.0) to reach pitches between the standard notes. Use REST for a rest.
       duration (int or float): How long the note lasts in the written score, as a float where 1.0 is a quarter note.
       dynamic (int, optional): How loud the note is, from 0 to 127.
       pan (int or float, optional): The stereo position, from 0.0 (left) through 0.5 (center) to 1.0 (right).
       length (int or float, optional): How long the note actually sounds, in the same units as duration. Defaults to 90% of the duration, so notes sound separate.
   """

   def __init__(self, value, duration, dynamic=85, pan=0.5, length=None):

      # establish note properties (for readability)
      self._type      = None      # "Pitch" or "Frequency", describes how pitch was set
      self._pitch     = None      # MIDI pitch (0 to 127) or REST
      self._frequency = None      # frequency (Hz) or REST
      self._pitchBend = None      # pitch bend value (-8191 to +8192)
      self._duration  = float(duration)  # duration (in seconds) - ensure it's a float
      self._dynamic   = dynamic   # dynamic (0 to 127)
      self._pan       = pan       # panning (0.0 to 1.0)

      # NOTE: If value is an int, it signifies a MIDI pitch;
      # otherwise, if it is a float, it signifies a frequency.

      # do some basic error checking
      if isinstance(value, int) and value != REST and (value < 0 or value > 127):
         raise TypeError(f"Note pitch should be an integer between 0 and 127 (it was {value}).")
      elif isinstance(value, float) and not value > 0.0:
         raise TypeError(f"Note frequency should be a float greater than 0.0 (it was {value}).")
      elif not isinstance(value, (int, float)):
         raise TypeError(f"Note first parameter should be a pitch (int) or a frequency (float) - it was {type(value)}.")

      # ensure duration is non-negative (but allow zero for chord notes)
      if self._duration < 0:
         self._duration = 0.1  # Set a small but audible duration as fallback
         print(f"Warning: Note duration must be non-negative. Using {self._duration} as default.")

      # set note length (if needed)
      if length is None:   # not provided?
         # handle the case where duration is zero (likely a chord note)
         if self._duration > 0:
            self._length = self._duration * DEFAULT_LENGTH_MULTIPLIER  # normally, duration * 0.9
         else:
            # for zero-duration notes (chord notes), set a small length
            self._length = 0.05  # Very small but non-zero length
      else:
         # ensure length is a float and non-negative
         self._length = float(length)
         if self._length < 0:
            self._length = self._duration * DEFAULT_LENGTH_MULTIPLIER
            print(f"Warning: Note length must be non-negative. Using calculated length {self._length}.")

      # now, construct the Note with the proper attributes
      if isinstance(value, int):
         self.setPitch(value)
      elif isinstance(value, float):
         self.setFrequency(value)

   def __str__(self):
      # notes can be either pitch or frequency based
      if self._type == "Pitch":
         value = self._pitch
      else:
         value = self._frequency

      # handle REST case where pitch is large negative number
      if self._pitch == REST:
         value = "REST"

      return f"Note(value = {value}, duration = {self._duration}, dynamic = {self._dynamic}, pan = {self._pan}, length = {self._length})"

   def __repr__(self):
      return self.__str__()

   def getPitch(self):
      """Return the note's pitch.

      Returns:
          pitch (int): The MIDI pitch, from 0 to 127, or REST for a rest.
      """
      pitch = self._pitch
      return pitch

   def setPitch(self, pitch):
      """Set the note's pitch.

      Args:
          pitch (int): The new MIDI pitch, from 0 to 127, or REST for a rest.
      """
      if not isinstance(pitch, int):
         raise TypeError(f"Note pitch should be an integer - (it was a {type(pitch)}).")

      elif not (0 <= pitch <= 127) and pitch != REST:
         raise TypeError(f"Note pitch should be an integer between 0 and 127 - (it was {pitch}).")

      # set pitch
      self._type  = "Pitch"  # remember pitch/frequency was set from a pitch
      self._pitch = pitch

      if pitch == REST:
         # pitch is a rest, so set frequency to rest
         self._frequency = REST
         self._pitchBend = OUR_PITCHBEND_NORMAL

      else:
         # otherwise, set frequency as normal
         self._frequency = noteToFreq(pitch)

   def getFrequency(self):
      """Return the note's pitch as a frequency.

      Returns:
          frequency (float): The pitch as a frequency, in hertz (8.17 to 12600.0).
      """
      frequency = self._frequency
      return frequency

   def setFrequency(self, frequency):
      """Set the note's pitch from a frequency.

      Setting a frequency lets the note land between the standard pitches.

      Args:
          frequency (float): The new pitch as a frequency, in hertz (8.17 to 12600.0).
      """
      # do some basic error checking
      if not isinstance(frequency, float):
         raise TypeError(f"Note frequency should be a float - (it was {type(frequency)}).")

      elif frequency <= 0.0:
         raise TypeError(f"Note frequency should be a float greater than 0.0 - (it was {frequency}).")

      # set pitch and frequency
      self._type = "Frequency"  # remember pitch/frequency was set from a frequency
      self._frequency = frequency
      self._pitch, self._pitchBend = freqToNote(frequency)

   def getPitchBend(self):
      """Return the note's pitch bend, the gap between its pitch and its exact frequency.

      Returns:
          pitchBend (int): The bend, in pitch bend units from -8191 to 8192, where 0 means no bend.
      """
      pitchBend = self._pitchBend
      return pitchBend

   def getDuration(self):
      """Return how long the note lasts in the written score.

      Returns:
          duration (int or float): The duration, as a float where 1.0 is a quarter note.
      """
      duration = self._duration
      return duration

   def setDuration(self, duration):
      """Set how long the note lasts in the written score.

      The note's length is adjusted to keep the same proportion to the duration.

      Args:
          duration (int or float): The new duration, as a float where 1.0 is a quarter note.
      """
      # Ensure the input is converted to float
      try:
         duration = float(duration)

         # Allow zero duration specifically for chord notes in jMusic format
         # but prevent negative durations
         if duration < 0:
            print(f"Warning: Note duration must be non-negative (got {duration}). Using 0.1 as fallback.")
            duration = 0.1
      except (ValueError, TypeError):
         print("Warning: Invalid duration value. Using 0.1 as fallback.")
         duration = 0.1

      # calculate length factor (ratio of length to duration)
      # this preserves the original articulation style
      lengthFactor = self._length / self._duration if self._duration > 0 else DEFAULT_LENGTH_MULTIPLIER

      # update duration and length
      self._duration = duration

      # only update length if duration is non-zero
      if duration > 0:
         self._length = duration * lengthFactor

   def getLength(self):
      """Return how long the note actually sounds.

      Duration is the note's written value; length is how long it actually sounds, normally
      about 90% of the duration so notes sound separate.

      Returns:
          length (int or float): The sounding length, in the same units as duration.
      """
      length = self._length
      return length

   def setLength(self, length):
      """Set how long the note actually sounds.

      Length is normally about 90% of the duration. Raise it toward the duration to make
      the note sound legato (smooth), or lower it to make it sound staccato (short).

      Args:
          length (int or float): The new sounding length, in the same units as duration.
      """
      # ensure the input is converted to float
      try:
         length = float(length)
         # allow zero length but prevent negative values
         if length < 0:
            print(f"Warning: Note length must be non-negative (got {length}). Using {self._duration * DEFAULT_LENGTH_MULTIPLIER} as fallback.")
            length = self._duration * DEFAULT_LENGTH_MULTIPLIER
      except (ValueError, TypeError):
         print(f"Warning: Invalid length value. Using {self._duration * DEFAULT_LENGTH_MULTIPLIER} as fallback.")
         length = self._duration * DEFAULT_LENGTH_MULTIPLIER

      self._length = length

   def getDynamic(self):
      """Return how loud the note is.

      Returns:
          dynamic (int): How loud the note is, from 0 to 127.
      """
      dynamic = self._dynamic
      return dynamic

   def setDynamic(self, dynamic):
      """Set how loud the note is.

      Args:
          dynamic (int): How loud to make the note, from 0 to 127.
      """
      if not isinstance(dynamic, int):
         raise TypeError(f"Note dynamic should be an integer - (it was {type(dynamic)}).")

      elif not (0 <= dynamic <= 127) and (dynamic != REST):
         raise TypeError(f"Note dynamic should be an integer between 0 and 127 - (it was {dynamic}).")

      self._dynamic = dynamic

   def getPan(self):
      """Return the note's stereo position.

      Returns:
          pan (int or float): The stereo position, from 0.0 (left) through 0.5 (center) to 1.0 (right).
      """
      pan = self._pan
      return pan

   def setPan(self, pan):
      """Set the note's stereo position.

      Args:
          pan (int or float): The new stereo position, from 0.0 (left) through 0.5 (center) to 1.0 (right).
      """
      if not (0.0 <= pan <= 1.0):
         raise TypeError(f"Note panning should be a float between 0.0 and 1.0 - (it was {pan})")

      self._pan = float( pan )

   def isRest(self):
      """Report whether the note is a rest.

      Returns:
          noteIsRest (bool): True if the note is a rest, False if it has a pitch.
      """
      noteIsRest = self._pitch == REST
      return noteIsRest

   def copy(self):
      """Return a copy of the note.

      Use this to make a version you can change while leaving the original untouched.

      Returns:
          noteCopy (Note): A new note with the same attributes as this one.
      """
      if self._type == "Pitch":
         value = self._pitch
      elif self._type == "Frequency":
         value = self._frequency
      else:
         # safety fallback (should not happen based on constructor logic)
         value = self._pitch if self._pitch is not None else REST

      noteCopy = Note(
         value,
         self._duration,
         self._dynamic,
         self._pan,
         self._length
      )
      return noteCopy


class Phrase():
   """Represent a phrase: a run of notes, one after another.

   Create it in a few ways:
   - Phrase() is empty.
   - Phrase(note) starts with a single Note.
   - Phrase(note, startTime) starts with a single Note and a start time.
   - Phrase(startTime) is empty but begins at a set time.

   A start time is in beats, where 0.0 is the start of the piece and 1.0 is a quarter
   note in.

   Args:
       arg1 (Note or int or float, optional): A first Note to add, or a start time in beats.
       arg2 (int or float, optional): A start time in beats, when arg1 is a Note.
   """

   def __init__(self, arg1=None, arg2=None):

      # initialize default phrase properties
      self._noteList      = []
      self._title         = "Untitled Phrase"
      self._instrument    = -1
      self._tempo         = -1
      self._startTime     = None

      # parse arguments by type - (arg1, arg2)
      # (None,  None)      is an empty phrase
      # (float, None)      is an empty phrase with a start time
      # (Note,  None)      is a phrase with a single note
      # (Note,  float)     is a phrase with a single note and a start time

      if isinstance(arg1, Note):
         self.addNote(arg1)

         if arg2 is not None:
            self.setStartTime(arg2)

      elif isinstance(arg1, (int, float)):
         self.setStartTime(arg1)

         if arg2 is not None:
            raise TypeError( "Error: 2 arguments were given when 1 was expected." )


   def __str__(self):
      # build header string
      phraseString = (
         f'\n<-------- PHRASE \'{self.getTitle()}\' '
         f'contains {self.getSize()} notes.  '
         f'Start time: {self.getStartTime()} -------->\n'
      )

      # add each note in the phrase
      for note in self.getNoteList():
         phraseString += (str(note) + "\n")

      return phraseString

   def __repr__(self):
      return self.__str__()

   def addNote(self, note, duration=None):
      """Add a note to the end of the phrase.

      Give a ready-made Note, or give a pitch and a duration and one is built for you.

      Args:
          note (Note or int or float): A Note to add, or a MIDI pitch (or frequency) to build one from.
          duration (int or float, optional): The note's duration (a float where 1.0 is a quarter note), used when building a note from a pitch.
      """
      if duration is not None:
         # two arguments were given, so create a new note with pitch and duration
         note = Note(note, duration)
         self._noteList.append(note)
      else:
         # one argument given - either a Note object or invalid input
         if isinstance(note, Note):
            self._noteList.append(note)
         else:
            raise TypeError(f"Phrase.addNote() expected a Note or (pitch, duration) - got {type(note)}.")

   def addChord(self, listOfPitches, duration, dynamic=85, pan=0.5, length=None):
      """Add a chord (several pitches sounded together) to the end of the phrase.

      Args:
          listOfPitches (list[int]): The chord's pitches, each a MIDI pitch from 0 to 127.
          duration (int or float): How long the chord lasts, as a float where 1.0 is a quarter note.
          dynamic (int, optional): How loud the chord is, from 0 to 127.
          pan (int or float, optional): The stereo position, from 0.0 (left) through 0.5 (center) to 1.0 (right).
          length (int or float, optional): How long the chord actually sounds, in the same units as duration. Defaults to 90% of the duration.
      """
      # ensure we have valid input
      if not listOfPitches:
         raise ValueError("Cannot add an empty chord - pitchList must contain at least one pitch.")

      # convert duration to float to ensure consistent handling
      duration = float(duration)

      # set chord length (if needed)
      if length is None:   # not provided?
         length = duration * DEFAULT_LENGTH_MULTIPLIER  # normally, duration * 0.9
      else:
         length = float(length)  # ensure it's a float

      # For chord notes, all notes but the last one have zero duration
      # This is how jMusic/MIDI handles chords - only the last note carries the duration

      # add all notes, except last one, with no duration and normal length
      # (exploiting how Play.midi() and Write.midi() work)
      for i in range(len(listOfPitches) - 1):
         n = Note(listOfPitches[i], 0, dynamic, pan, length)
         self.addNote(n)

      # now, add last note with proper duration (and length)
      n = Note(listOfPitches[-1], duration, dynamic, pan, length)
      self.addNote(n)

   def addNoteList(self, listOfPitches, listOfDurations, listOfDynamics=[], listOfPannings=[], listOfLengths=[]):
      """Add many notes to the end of the phrase at once.

      The lists are parallel: the first note takes the first pitch, the first duration, and
      so on. A pitch may itself be a list, which adds a chord. The dynamic, panning, and
      length lists are optional.

      Args:
          listOfPitches (list[int or list[int]]): The notes' pitches, each a MIDI pitch (or a list of pitches for a chord).
          listOfDurations (list[int or float]): The notes' durations, each a float where 1.0 is a quarter note.
          listOfDynamics (list[int], optional): The notes' dynamics, each from 0 to 127. Defaults to full for every note.
          listOfPannings (list[int or float], optional): The notes' stereo positions, each from 0.0 (left) to 1.0 (right). Defaults to center.
          listOfLengths (list[int or float], optional): The notes' sounding lengths. Defaults to 90% of each duration.
      """
      # if dynamics was not provided, construct it with max value
      if listOfDynamics == []:
         listOfDynamics = [85] * len( listOfPitches )

      # if panoramics was not provided, construct it at CENTER
      if listOfPannings == []:
         listOfPannings = [0.5] * len( listOfPitches )

      # if note lengths was not provided, construct it at 90% of note duration
      if listOfLengths == []:
         listOfLengths = [
            duration * DEFAULT_LENGTH_MULTIPLIER for duration in listOfDurations
         ]

      # check if provided lists have equal lengths
      if not ( len(listOfPitches)    ==
              len(listOfDurations)  ==
              len(listOfDynamics)   ==
              len(listOfPannings) ==
              len(listOfLengths) ):
         raise ValueError( "addNoteList() The provided lists should have the " \
                          + "same length." )

      # traverse the pitch list and handle each entry appropriately
      for i in range( len(listOfPitches) ):

         # is it a chord or a note?

         if isinstance(listOfPitches[i], list):
            # chord, so pass its values to addChord()
            self.addChord(
                listOfPitches[i],
                listOfDurations[i],
                listOfDynamics[i],
                listOfPannings[i],
                listOfLengths[i]
            )

         else:
            # note, construct a new note and add it
            n = Note(
                listOfPitches[i],
                listOfDurations[i],
                listOfDynamics[i],
                listOfPannings[i],
                listOfLengths[i]
            )
            self.addNote(n)

   def getNoteList(self):
      """Return the phrase's notes.

      Returns:
          noteList (list[Note]): The notes in the phrase.
      """
      noteList = self._noteList
      return noteList

   # aliases for backwards compatibility with jmusic api
   addNoteArray = addNoteList
   getNoteArray = getNoteList

   def getInstrument(self):
      """Return the phrase's instrument.

      Returns:
          instrument (int): The instrument (timbre), as a MIDI instrument number from 0 to 127.
      """
      instrument = self._instrument
      return instrument

   def setInstrument(self, instrument):
      """Set the phrase's instrument.

      Args:
          instrument (int): The instrument (timbre), as a MIDI instrument number from 0 to 127.
      """
      if not isinstance(instrument, int):
         raise TypeError(f"Instrument should be an integer - (it was {type(instrument)}).")

      if instrument == -1:
         pass

      elif not (0 <= instrument <= 127):
         raise TypeError(f"Instrument should be an integer between 0 and 127 - (it was {instrument}).")

      self._instrument = instrument

   def getTempo(self):
      """Return the phrase's tempo.

      Returns:
          tempo (int or float): The tempo, in beats per minute.
      """
      tempo = self._tempo
      return tempo

   def setTempo(self, tempo):
      """Set the phrase's tempo.

      Args:
          tempo (int or float): The new tempo, in beats per minute.
      """
      self._tempo = float(tempo)

   def getTitle(self):
      """Return the phrase's title.

      Returns:
          title (str): The phrase's title.
      """
      title = self._title
      return title

   def setTitle(self, title):
      """Set the phrase's title.

      Args:
          title (str): The new title.
      """
      if not isinstance(title, str):
         raise TypeError(f"Title should be a string - (it was {type(title)}).")

      self._title = title

   def setDynamic(self, dynamic):
      """Set how loud every note in the phrase is.

      Args:
          dynamic (int): How loud to make every note, from 0 to 127.
      """
      for note in self._noteList:
         note.setDynamic( dynamic )

   def setPan(self, pan):
      """Set the stereo position of every note in the phrase.

      Args:
          pan (int or float): The stereo position, from 0.0 (left) through 0.5 (center) to 1.0 (right).
      """
      for note in self._noteList:
         note.setPan(pan)

   def getStartTime(self):
      """Return when the phrase starts.

      Returns:
          startTime (int or float): The start time, in beats, where 0.0 is the start of the piece.
      """
      # do not mutate internal state when unset; default display value is 0.0
      if self._startTime is None:
         startTime = 0.0
      else:
         startTime = self._startTime
      return startTime

   def setStartTime(self, startTime):
      """Set when the phrase starts.

      Args:
          startTime (int or float): The new start time, in beats, where 0.0 is the start of the piece.
      """
      if startTime is None:
         startTime = 0.0

      self._startTime = float( startTime )

   def getEndTime(self):
      """Return when the phrase ends.

      Returns:
          endTime (int or float): The end time, in beats.
      """
      # sum duration of every note in this phrase
      endTime = self.getStartTime()

      for note in self.getNoteList():
         endTime += note.getDuration()

      return endTime

   def getSize(self):
      """Return how many notes are in the phrase.

      Returns:
          noteCount (int): The number of notes.
      """
      noteCount = len(self._noteList)
      return noteCount

   def getNote(self, index):
      """Return the note at a given position, without changing the phrase.

      Args:
          index (int): The note's position, where 0 is the first note.

      Returns:
          note (Note): The note at that position.
      """
      note = self._noteList[index]
      return note

   def removeNote(self, index):
      """Remove the note at a given position from the phrase.

      Args:
          index (int): The note's position, where 0 is the first note.

      Returns:
          removedNote (Note): The note that was removed.
      """
      removedNote = self._noteList.pop(index)
      return removedNote

   def getNoteStartTime(self, index):
      """Return when the note at a given position starts.

      Args:
          index (int): The note's position, where 0 is the first note.

      Returns:
          startTime (int or float): The note's start time, in beats from the start of the phrase.
      """
      # sum duration of every note up to specified index
      startTime = 0

      for i in range( index ):
         startTime += self._noteList[i].getDuration()

      return startTime

   def getLowestPitch(self):
      """Return the pitch of the lowest note in the phrase.

      Returns:
          lowestPitch (int): The lowest pitch, as a MIDI pitch.
      """
      # check every note in this phrase for the lowest pitch
      lowestPitch = float(np.inf)

      for note in self._noteList:
         if note.getPitch() < lowestPitch:
               lowestPitch = note.getPitch()

      return lowestPitch

   def getHighestPitch(self):
      """Return the pitch of the highest note in the phrase.

      Returns:
          highestPitch (int): The highest pitch, as a MIDI pitch.
      """
      # check every note in this phrase for the highest pitch
      highestPitch = float(-np.inf)

      for note in self._noteList:
         if note.getPitch() > highestPitch:
               highestPitch = note.getPitch()

      return highestPitch

   def getShortestDuration(self):
      """Return the duration of the shortest note in the phrase.

      Returns:
          shortestDuration (int or float): The shortest duration, as a float where 1.0 is a quarter note.
      """
      # check every note in this phrase for the shortest duration
      shortestDuration = float(np.inf)

      for note in self._noteList:
         if note.getDuration() < shortestDuration:
               shortestDuration = note.getDuration()

      return shortestDuration

   def getLongestDuration(self):
      """Return the duration of the longest note in the phrase.

      Returns:
          longestDuration (int or float): The longest duration, as a float where 1.0 is a quarter note.
      """
      # check every note in this phrase for the longest duration
      longestDuration = float(-np.inf)

      for note in self._noteList:
         if note.getDuration() > longestDuration:
               longestDuration = note.getDuration()

      return longestDuration

   def copy(self):
      """Return a copy of the phrase.

      Use this to make a version you can change while leaving the original untouched.

      Returns:
          newPhrase (Phrase): A new phrase with the same notes and attributes as this one.
      """
      # create a new phrase
      newPhrase = Phrase()

      # copy this phrase's properties
      newPhrase.setTitle( self.getTitle() )
      newPhrase.setInstrument( self.getInstrument() )
      newPhrase.setTempo( self.getTempo() )
      newPhrase.setStartTime( self.getStartTime() )

      # copy all notes in this phrase
      for note in self.getNoteList():
         newPhrase.addNote( note.copy() )

      return newPhrase

   def empty(self):
      """Remove every note from the phrase.
      """
      self._noteList = []


class Part():
   """Represent a part: the phrases played by one instrument.

   Create it in a few ways:
   - Part() is empty.
   - Part(instrument) is empty, with the given instrument.
   - Part(instrument, channel) is empty, with the given instrument and MIDI channel.
   - Part(title, instrument, channel) is empty, with a title, instrument, and channel.
   - Part(phrase) starts with one phrase.

   Args:
       arg1 (Phrase or int or str, optional): A first Phrase, an instrument number (0 to 127), or a title.
       arg2 (int, optional): An instrument number, or a MIDI channel (0 to 15) when arg1 is a title.
       arg3 (int, optional): A MIDI channel (0 to 15), when a title and instrument are given.
   """

   def __init__(self, arg1=None, arg2=None, arg3=None):

      # initialize default part properties
      self._phraseList = []
      self._title      = "Untitled Part"
      self._instrument = -1
      self._channel    = 0
      self._tempo      = -1
      self._volume     = -1

      # parse arguments by type - (arg1, arg2, arg3)
      # (None, None, None) is an empty part
      # (int,  None, None) is an empty part with an instrument
      # (int,  int,  None) is an empty part with an instrument and channel
      # (str,  int,  int ) is an empty part a title, instrument, and channel
      # (Phrase, None, None) is a part with a single phrase

      if type(arg1) is int:
         self.setInstrument(arg1)

         if type(arg2) is int:
            self.setChannel(arg2)

         if arg3 is not None:
            raise TypeError( "Error: 3 arguments were given when 2 were expected." )

      elif isinstance(arg1, str):
         self.setTitle(arg1)

         if type(arg2) is int:
            self.setInstrument(arg2)

         if type(arg3) is int:
            self.setChannel(arg3)

      elif isinstance(arg1, Phrase):
         self.addPhrase(arg1)

         tempo = arg1.getTempo()
         if tempo > 0:
            self.setTempo(tempo)

   def __str__(self):
      # build header string
      partString = (
         f'\n<----- PART \'{self.getTitle()}\' contains {self.getSize()} phrases.  ----->\n'
         f'Channel = {self.getChannel()}\n'
         f'Instrument = {self.getInstrument()}\n'
      )

      # add each phrase in the part
      displayStartTime = 0.0

      for phrase in self.getPhraseList():
         # create a copy of the phrase with an adjusted start time for display purposes
         tempPhrase = phrase.copy()
         tempPhrase.setStartTime(displayStartTime)
         partString += str(tempPhrase)
         displayStartTime += phrase.getEndTime()

      return partString

   def __repr__(self):
      return self.__str__()

   def addPhrase(self, phrase):
      """Add a phrase to the part.

      If the phrase has no set start time, it is placed at the end of the part.

      Args:
          phrase (Phrase): The phrase to add.
      """
      if type( phrase ) is not Phrase:
         raise TypeError(f"addPhrase(phrase) parameter should be a Phrase - (it was {type(phrase)}).")

      # if phrase has no explicit start time, place it sequentially
      if getattr(phrase, "_startTime", None) is None:
         # first phrase starts at 0.0, subsequent phrases start after previous content
         if not self.getPhraseList():
            phrase.setStartTime(0.0)  # start the first phrase at time 0
         else:
            # subsequent phrases start after previous content
            phrase.setStartTime(self.getEndTime())

      self._phraseList.append( phrase )

   def addPhraseList(self, phraseList):
      """Add several phrases to the part at once.

      Any phrase with no set start time is placed at the end of the part.

      Args:
          phraseList (list[Phrase]): The phrases to add.
      """
      for phrase in phraseList:
         self.addPhrase(phrase)

   def getPhraseList(self):
      """Return the part's phrases.

      Returns:
          phraseList (list[Phrase]): The phrases in the part.
      """
      phraseList = self._phraseList
      return phraseList

   # aliases for backwards compatibility with jmusic api
   addPhraseArray = addPhraseList
   getPhraseArray = getPhraseList

   def getTitle(self):
      """Return the part's title.

      Returns:
          title (str): The part's title.
      """
      title = self._title
      return title

   def setTitle(self, title):
      """Set the part's title.

      Args:
          title (str): The new title.
      """
      if not isinstance(title , str):
         raise TypeError(f"Part title should be a string - (it was {type(title)})")

      self._title = title

   def getInstrument(self):
      """Return the part's instrument.

      Returns:
          instrument (int): The instrument (timbre), as a MIDI instrument number from 0 to 127.
      """
      instrument = self._instrument
      return instrument

   def setInstrument(self, instrument):
      """Set the part's instrument.

      Args:
          instrument (int): The instrument (timbre), as a MIDI instrument number from 0 to 127.
      """
      if not isinstance(instrument , int):
         raise TypeError(f"Instrument should be an integer - (it was {type(instrument)})")

      elif instrument == -1:
         # -1 uses the global instrument for this part's channel
         pass

      elif not ( 0 <= instrument <= 127 ):
         # MIDI instruments are between 0 and 127
         raise TypeError(f"Instrument should be an integer between 0 and 127 - (it was {instrument})")

      self._instrument = instrument

   def getChannel(self):
      """Return the part's MIDI channel.

      Returns:
          channel (int): The MIDI channel, from 0 to 15.
      """
      channel = self._channel
      return channel

   def setChannel(self, channel):
      """Set the part's MIDI channel.

      Args:
          channel (int): The MIDI channel, from 0 to 15.
      """
      if not isinstance(channel, int):
         raise TypeError(f"Channel should be an integer - (it was {type(channel)})")

      elif not (0 <= channel <= 15):
         raise TypeError(f"Channel should be an integer between 0 and 15 - (it was {channel})")

      self._channel = channel

   def getTempo(self):
      """Return the part's tempo.

      Returns:
          tempo (int or float): The tempo, in beats per minute.
      """
      tempo = self._tempo
      return tempo

   def setTempo(self, tempo):
      """Set the part's tempo.

      Args:
          tempo (int or float): The new tempo, in beats per minute.
      """
      self._tempo = float(tempo)

   def getVolume(self):
      """Return the part's volume.

      Returns:
          volume (int): The volume, from 0 to 127.
      """
      volume = self._volume
      return volume

   def setVolume(self, volume):
      """Set the part's volume.

      Args:
          volume (int): The new volume, from 0 to 127.
      """
      if not isinstance(volume, int):
         raise TypeError(f"Volume should be an integer - (it was {type(volume)})")

      elif volume == -1:
         volume = 127

      elif not (0 <= volume <= 127):
         raise TypeError(f"Volume should be an integer between 0 and 127 - (it was {volume})")

      self._volume = volume

   def getStartTime(self):
      """Return when the part starts.

      Returns:
          startTime (int or float): The start time, in beats, where 0.0 is the start of the piece.
      """
      startTime = float(np.inf)

      # find the earliest starting time of all phrases in this part
      for phrase in self.getPhraseList():
         startTime = min( startTime, phrase.getStartTime() )

      if startTime is None:
         startTime = 0.0

      return startTime

   def getEndTime(self):
      """Return when the part ends.

      Returns:
          endTime (int or float): The end time, in beats. An empty part ends at 0.0.
      """
      # check if the part is empty
      if not self.getPhraseList():
         return 0.0  # return 0.0 for an empty part instead of -infinity

      endTime = float(-np.inf)

      # find the latest ending time of all phrases in this part
      for phrase in self.getPhraseList():
         endTime = max( endTime, phrase.getEndTime() )

      return endTime

   def getSize(self):
      """Return how many phrases are in the part.

      Returns:
          phraseCount (int): The number of phrases.
      """
      phraseCount = len(self.getPhraseList())
      return phraseCount

   def setPan(self, panning):
      """Set the stereo position of every note in the part.

      Args:
          panning (int or float): The stereo position, from 0.0 (left) through 0.5 (center) to 1.0 (right).
      """
      for phrase in self.getPhraseList():
         phrase.setPan( panning )

   def setDynamic(self, dynamic):
      """Set how loud every note in the part is.

      Args:
          dynamic (int): How loud to make every note, from 0 to 127.
      """
      for phrase in self.getPhraseList():
         phrase.setDynamic( dynamic )

   def copy(self):
      """Return a copy of the part.

      Use this to make a version you can change while leaving the original untouched.

      Returns:
          newPart (Part): A new part with the same phrases and attributes as this one.
      """
      # create a new part
      newPart = Part()

      # copy this part's properties
      newPart.setTitle( self.getTitle() )
      newPart.setInstrument( self.getInstrument() )
      newPart.setChannel( self.getChannel() )
      newPart.setTempo( self.getTempo() )
      newPart.setVolume( self.getVolume() )

      # copy all phrases in this part
      for phrase in self.getPhraseList():
         newPart.addPhrase( phrase.copy() )

      return newPart

   def empty(self):
      """Remove every phrase from the part.
      """
      self._phraseList = []


class Score():
   """Represent a score: a whole piece, made of parts played together.

   Create it in a few ways:
   - Score() is empty.
   - Score(title) is empty, with a title.
   - Score(tempo) is empty, with a tempo in beats per minute.
   - Score(title, tempo) is empty, with a title and a tempo.
   - Score(part) starts with one part.

   Args:
       arg1 (Part or str or int, optional): A first Part, a title, or a tempo in beats per minute.
       arg2 (int, optional): A tempo in beats per minute, when arg1 is a title.
   """

   def __init__(self, arg1=None, arg2=None):

      # initialize default score properties
      self._partList      = []
      self._title         = "Untitled Score"
      self._tempo         = 60.0
      self._volume        = 85
      self._timeSignature = [4, 4]
      self._keySignature  = 0
      self._keyQuality    = 0

      # parse arguments by type - (arg1, arg2)
      # (None, None) is an empty score
      # (str,  None) is an empty score with a title
      # (str,  int)  is an empty score with a title and tempo
      # (int,  None) is an empty score with a tempo
      # (Part, None) is a score with a single part

      if type(arg1) is str:
         self.setTitle( arg1 )

         if arg2 is not None:
            self.setTempo(arg2)

      elif type(arg1) is Part:
         self.addPart(arg1)

         tempo = arg1.getTempo()
         if tempo > 0:
            self.setTempo(tempo)

      elif type(arg1) is int:
         self.setTempo(arg1)

   def __str__(self):
      # build header string
      scoreString = (
         f'\n<***** SCORE \'{self.getTitle()}\' '
         f'contains {self.getSize()} parts. ****>\n'
         f'Score Tempo = {self.getTempo()} bpm\n'
      )

      # add each part in the score
      for part in self.getPartList():
         scoreString += str(part) + "\n"

      return scoreString

   def __repr__(self):
      return self.__str__()

   def addPart(self, part):
      """Add a part to the score.

      Args:
          part (Part): The part to add.
      """
      if type(part) is not Part:
         raise TypeError(f'addPart(part) parameter should be a Part - (it was {type(part)}).')

      self._partList.append(part)

   def addPartList(self, partList):
      """Add several parts to the score at once.

      Args:
          partList (list[Part]): The parts to add.
      """
      for part in partList:
         self.addPart( part )

   def getPartList(self):
      """Return the score's parts.

      Returns:
          partList (list[Part]): The parts in the score.
      """
      partList = self._partList
      return partList

   # aliases for backwards compatibility with jmusic api
   addPartArray = addPartList
   getPartArray = getPartList

   def getTitle(self):
      """Return the score's title.

      Returns:
          title (str): The score's title.
      """
      title = self._title
      return title

   def setTitle(self, title):
      """Set the score's title.

      Args:
          title (str): The new title.
      """
      if not isinstance( title , str):
         raise TypeError(f'Score title should be a string - (it was {type(title)}).')

      self._title = title

   def getTempo(self):
      """Return the score's tempo.

      Returns:
          tempo (int or float): The tempo, in beats per minute.
      """
      tempo = self._tempo
      return tempo

   def setTempo(self, tempo):
      """Set the score's tempo.

      Args:
          tempo (int or float): The new tempo, in beats per minute.
      """
      self._tempo = float(tempo)

   def getVolume(self):
      """Return the score's volume.

      Returns:
          volume (int): The volume, from 0 to 127.
      """
      volume = self._volume
      return volume

   def setVolume(self, volume):
      """Set the score's volume.

      Args:
          volume (int): The new volume, from 0 to 127.
      """
      if not isinstance( volume , int):
         raise TypeError(f'Volume should be an integer - (it was {type(volume)}).')

      elif not (0 <= volume <= 127):
         raise TypeError(f'Volume should be an integer between 0 and 127 - (it was {volume}).')

      self._volume = volume

   def getNumerator(self):
      """Return the top number of the score's time signature.

      Returns:
          numerator (int): The time signature numerator (the number of beats per measure).
      """
      numerator = self._timeSignature[0]
      return numerator

   def getDenominator(self):
      """Return the bottom number of the score's time signature.

      Returns:
          denominator (int): The time signature denominator (the note value that counts as one beat).
      """
      denominator = self._timeSignature[1]
      return denominator

   def setTimeSignature(self, numerator, denominator):
      """Set the score's time signature.

      For example, setTimeSignature(3, 4) sets 3/4 time.

      Args:
          numerator (int): The number of beats per measure (the top number).
          denominator (int): The note value that counts as one beat (the bottom number).
      """
      self._timeSignature = [numerator, denominator]

   def getKeyQuality(self):
      """Return the score's key quality (major or minor).

      Returns:
          keyQuality (int): 0 for major, 1 for minor.
      """
      keyQuality = self._keyQuality
      return keyQuality

   def setKeyQuality(self, quality):
      """Set the score's key quality (major or minor).

      Args:
          quality (int): 0 for major, 1 for minor.
      """
      if not isinstance( quality , int):
         raise TypeError(f'Key quality should be an integer - (it was {type(quality)}).')

      elif not (quality == 0 or quality == 1):
         raise TypeError(f'Key quality should be either 0 or 1 - (it was {quality}).')

      self._keyQuality = quality

   def getKeySignature(self):
      """Return the score's key signature.

      Returns:
          keySignature (int): The key signature: 0 is the key of C, a positive number counts sharps, and a negative number counts flats.
      """
      keySignature = self._keySignature
      return keySignature

   def setKeySignature(self, signature):
      """Set the score's key signature.

      Args:
          signature (int): The key signature: 0 is the key of C, a positive number counts sharps, and a negative number counts flats.
      """
      if not isinstance(signature, int):
         raise TypeError(f'Key signature should be an integer - (it was {type(signature)}).')

      elif not (-8 < signature < 8):
         raise TypeError(f'Key signature should be an integer between -7 and 7 - (it was {signature}).')

      self._keySignature = signature

   def getStartTime(self):
      """Return when the score starts.

      Returns:
          startTime (int or float): The start time, in beats, where 0.0 is the start of the piece.
      """
      startTime = float(np.inf)

      # find the earliest starting time of all parts in this score
      for part in self.getPartList():
         startTime = min( startTime, part.getStartTime() )

      return startTime

   def getEndTime(self):
      """Return when the score ends.

      Returns:
          endTime (int or float): The end time, in beats.
      """
      endTime = float(-np.inf)

      # find the latest ending time of all parts in this score
      for part in self.getPartList():
         endTime = max( endTime, part.getEndTime() )

      return endTime

   def getSize(self):
      """Return how many parts are in the score.

      Returns:
          partCount (int): The number of parts.
      """
      partCount = len(self.getPartList())
      return partCount

   def setPan(self, pan):
      """Set the stereo position of every note in the score.

      Args:
          pan (int or float): The stereo position, from 0.0 (left) through 0.5 (center) to 1.0 (right).
      """
      for part in self.getPartList():
         part.setPan(pan)

   def copy(self):
      """Return a copy of the score.

      Use this to make a version you can change while leaving the original untouched.

      Returns:
          newScore (Score): A new score with the same parts and attributes as this one.
      """
      # create a new score
      newScore = Score()
      # copy this score's properties
      newScore.setTitle( self.getTitle() )
      newScore.setTempo( self.getTempo() )
      newScore.setVolume( self.getVolume() )
      newScore.setTimeSignature( self.getNumerator(), self.getDenominator() )
      newScore.setKeySignature( self.getKeySignature() )
      newScore.setKeyQuality( self.getKeyQuality() )

      # copy all parts in this score
      for part in self.getPartList():
         newScore.addPart( part.copy() )

      return newScore

   def empty(self):
      """Remove every part from the score.
      """
      self._partList.clear()


#######################################################################################
##### Play ############################################################################
#######################################################################################

# track settings on each channel for _MIDI_SYNTH
_currentInstrument = [0] * 16     # default to piano for all 16 channels
_currentVolume = [100] * 16       # default to moderate volume for all channels
_currentPanning = [64] * 16       # default to center for all channels
_currentPitchbend = [OUR_PITCHBEND_NORMAL] * 16   # default to no bend for all channels
_notesCurrentlyPlaying = []       # tracks notes currently on
_MAX_NOTES_ON = 255   # maximum notes allowed without corresponding noteOff

# WeakSet to track note-on timers for allNotesOff() functionality
# This allows us to distinguish between scheduled and active notes
_noteOnTimers = weakref.WeakSet()

# WeakSet to track note-off timers for allNotesOff() functionality
# When timers complete naturally, they are automatically removed from this set
# preventing memory leaks while still allowing allNotesOff() to stop active timers
_noteOffTimers = weakref.WeakSet()

# Dictionary to map note-off timers to their note information (pitch, channel, startTime)
# This allows allNotesOff() to selectively stop only timers for currently playing notes
# (avoids deleting note-off timers for notes that haven't started yet)
_noteOffTimerInfo = weakref.WeakKeyDictionary()

class Play:
   """Play and stop sounds through the computer's synthesizer.

   Play is a static utility. Call its methods on the class itself, for example
   Play.midi(). It plays music library material (Note, Phrase, Part, or Score), starts
   and stops individual notes and frequencies, and sets each channel's instrument,
   volume, and panning. It can also play material using AudioSamples in place of the
   synthesizer.
   """

   @staticmethod
   def midi(material):
      """Play music library material through the synthesizer.

      Args:
          material (Note, Phrase, Part, or Score): The music to play.
      """
      # do necessary datatype wrapping (MidiSynth() expects a Score)
      if isinstance(material, Note):
         material = Phrase(material)
      if isinstance(material, Phrase):   # no elif - we need to successively wrap from Note to Score
         material = Part(material)
         material.setInstrument(-1)     # indicate no default instrument (needed to access global instrument)
      if isinstance(material, Part):     # no elif - we need to successively wrap from Note to Score
         material = Score(material)
      if isinstance(material, Score):
         # we are good - let's play it then!
         score = material   # by now, material is a score, so create an alias (for readability)

         # loop through all parts and phrases to get all notes
         noteList = []               # holds all notes
         tempo = score.getTempo()    # get global tempo (can be overidden by part and phrase tempos)
         for part in score.getPartList():   # traverse all parts
            channel = part.getChannel()        # get part channel
            instrument = Play.getInstrument(channel)  # get global instrument for this channel
            if part.getInstrument() > -1:      # has the part instrument been set?
               instrument = part.getInstrument()  # yes, so it takes precedence
            if part.getTempo() > -1:           # has the part tempo been set?
               tempo = part.getTempo()            # yes, so update tempo
            for phrase in part.getPhraseList():   # traverse all phrases in part
               if phrase.getInstrument() > -1:        # is this phrase's instrument set?
                  instrument = phrase.getInstrument()    # yes, so it takes precedence
               if phrase.getTempo() > -1:          # has the phrase tempo been set?
                  tempo = phrase.getTempo()           # yes, so update tempo

               # time factor to convert time from jMusic Score units to milliseconds
               # (this needs to happen here every time, as we may be using the tempo from score, part, or phrase)
               FACTOR = 1000 * 60.0 / tempo

               # process notes in this phrase
               startTime = phrase.getStartTime() * FACTOR   # in milliseconds
               for note in phrase.getNoteList():
                  frequency = note.getFrequency()
                  panning = note.getPan()
                  panning = mapValue(panning, 0.0, 1.0, 0, 127)    # map from range 0.0..1.0 (Note panning) to range 0..127
                  start = int(startTime)                           # remember this note's start time (in milliseconds)

                  # NOTE:  Below we use note length as opposed to duration (getLength() vs. getDuration())
                  # since note length gives us a more natural sounding note (with proper decay), whereas
                  # note duration captures the more formal (printed score) duration (which sounds unnatural).
                  duration = int(note.getLength() * FACTOR)   # convert to milliseconds
                  startTime = startTime + note.getDuration() * FACTOR   # update start time (in milliseconds)
                  velocity = note.getDynamic()

                  # accumulate non-REST notes
                  if (frequency != REST):
                     noteList.append((start, duration, frequency, velocity, channel, instrument, panning))   # put start time first and duration second, so we can sort easily by start time (below),
                     # and so that notes that are members of a chord as denoted by having a duration of 0 come before the note that gives the specified chord duration

         # sort notes by start time
         noteList.sort()

         # schedule playing all notes in noteList
         chordNotes = []      # used to process notes belonging in a chord
         for start, duration, pitch, velocity, channel, instrument, panning in noteList:
            # set appropriate instrument for this channel
            Play.setInstrument(instrument, channel)

            # handle chord (if any)
            # Chords are denoted by a sequence of notes having the same start time and 0 duration (except the last note
            # of the chord).
            if duration == 0:   # does this note belong in a chord?
               chordNotes.append([start, duration, pitch, velocity, channel, panning])  # add it to the list of chord notes

            elif chordNotes == []:   # is this a regular, solo note (not part of a chord)?

               # yes, so schedule it to play via a Play.note event
               Play.note(pitch, start, duration, velocity, channel, panning)
               #print "Play.note(" + str(pitch) + ", " + str(int(start * FACTOR)) + ", " + str(int(duration * FACTOR)) + ", " + str(velocity) + ", " + str(channel) + ")"

            else:   # note has a normal duration and it is part of a chord

               # first, add this note together with this other chord notes
               chordNotes.append([start, duration, pitch, velocity, channel, panning])

               # now, schedule all notes in the chord list using last note's duration
               for start, ignoreThisDuration, pitch, velocity, channel, panning in chordNotes:
                  # schedule this note using chord's duration (provided by the last note in the chord)
                  Play.note(pitch, start, duration, velocity, channel, panning)
                  #print "Chord: Play.note(" + str(pitch) + ", " + str(int(start * FACTOR)) + ", " + str(int(duration * FACTOR)) + ", " + str(velocity) + ", " + str(channel) + ")"
               # now, all chord notes have been scheduled

               # so, clear chord notes to continue handling new notes (if any)
               chordNotes = []

         # now, all notes have been scheduled for future playing - scheduled notes can always be stopped using
         # JEM's stop button - this will stop all running timers (used by Play.note() to schedule playing of notes)
         #print "Play.note(" + str(pitch) + ", " + str(int(start * FACTOR)) + ", " + str(int(duration * FACTOR)) + ", " + str(velocity) + ", " + str(channel) + ")"

      else:   # error check
         print(f'Play.midi(): Unrecognized type {type(material)}, expected Note, Phrase, Part, or Score.')

   @staticmethod
   # NOTE:  Here we connect noteOn() and frequencyOn() with noteOnPitchBend() to allow for
   # playing microtonal music.  Although this may seem as cyclical (i.e., that in noteOn() we
   # convert pitch to frequency, and then call frequencyOn() which convert the frequency back to pitch,
   # so that it can call noteOnPitchBend() ), this is the only way we can make everything work.
   # We are constrained by the fact that jMusic Note objects are limited in how they handle pitch and
   # frequency (i.e., that creating a Note with pitch will set the Note's corresponding frequency,
   # but not the other way around), and the fact that we can call Note.getFrequency() above in Play.midi()
   # without problem, but NOT Note.getPitch(), which will crash if the Note was instantiated with a frequency
   # (i.e., pitch is not available / set).
   # Therefore, we need to make the run about here, so that we keep everything else easier to code / maintain,
   # and also keep the API (creating and play notes) simpler.  So, do NOT try to simplify the following code,
   # as it is the only way (I think) that can make everything else work simply - also see Play.midi().
   def noteOn(pitch, velocity=100, channel=0, panning=-1):
      """Start a pitch sounding, and leave it sounding.

      The note keeps playing until you stop it with Play.noteOff().

      Args:
          pitch (int or float): A MIDI pitch from 0 to 127, or a frequency in hertz (8.17 to 12600.0) to reach pitches between the standard notes.
          velocity (int, optional): How loud the note is, from 0 to 127.
          channel (int, optional): The channel to play on, from 0 to 15.
          panning (int, optional): Stereo position from 0 (left) to 127 (right); -1 uses the global panning.
      """
      if (isinstance(pitch, int)) and (0 <= pitch <= 127):   # a MIDI pitch?
         # yes, so convert pitch from MIDI number (int) to Hertz (float)
         pitch = noteToFreq(pitch)

      if isinstance(pitch, float):        # a pitch in Hertz?
         Play.frequencyOn(pitch, velocity, channel, panning)  # start it

      else:
         print(f'Play.noteOn(): Unrecognized pitch {pitch}, expected MIDI pitch from 0 to 127 (int), or frequency in Hz from 8.17 to 12600.0 (float).')

   @staticmethod
   def frequencyOn(frequency, velocity=100, channel=0, panning=-1):
      """Start a frequency sounding, and leave it sounding.

      Stop it with Play.frequencyOff(). Play only one frequency per channel at a time:
      since this uses pitch bend, it affects every other note sounding on the channel.

      Args:
          frequency (float): The frequency to play, in hertz (8.17 to 12600.0).
          velocity (int, optional): How loud the note is, from 0 to 127.
          channel (int, optional): The channel to play on, from 0 to 15.
          panning (int, optional): Stereo position from 0 (left) to 127 (right); -1 uses the global panning.
      """
      if (isinstance(frequency, float)) and (8.17 <= frequency <= 12600.0): # a pitch in Hertz (within MIDI pitch range 0 to 127)?
         pitch, bend = freqToNote( frequency )                     # convert to MIDI note and pitch bend
         Play.noteOnPitchBend(pitch, bend, velocity, channel, panning)      # and start it

      else:
         print(f'Play.frequencyOn(): Invalid frequency {frequency}, expected frequency in Hz from 8.17 to 12600.0 (float).')

   @staticmethod
   def noteOnPitchBend(pitch, bend=0, velocity=100, channel=0, panning=-1):
      """Start a pitch sounding with a pitch bend, and leave it sounding.

      Stop it with Play.noteOff().

      Args:
          pitch (int): A MIDI pitch, from 0 to 127.
          bend (int, optional): How far to bend the pitch, in pitch bend units from -8191 (full down) to 8192 (full up), where 0 means no bend.
          velocity (int, optional): How loud the note is, from 0 to 127.
          channel (int, optional): The channel to play on, from 0 to 15.
          panning (int, optional): Stereo position from 0 (left) to 127 (right); -1 uses the global panning.
      """
      # check if pitch bend is within expected range
      if OUR_PITCHBEND_MIN <= bend <= OUR_PITCHBEND_MAX:

         # we are OK, so set pitchbend on the synthesizer!
         Play.setPitchBend(bend, channel)

         # set panning if we have one
         if panning != -1:                  # if we have a specific panning...
            Play.setPanning(panning, channel)  # set it

         # GUARDRAIL: clean up old notes if user isn't turning notes off themselves
         # this will prevent tinysoundfont from crashing
         Play._cleanupOldNotes()

         # keep track of how many overlapping instances of this pitch are currently sounding on this channel
         # so that we turn off only the last one - also see frequencyOff()
         noteID = (pitch, channel)              # create an ID using pitch-channel pair
         _notesCurrentlyPlaying.append(noteID)   # add this note instance to list

         # start note on synthesizer
         _MIDI_SYNTH.noteon(channel, pitch, velocity)

      else:     # bend was outside expected range
         error_msg = f'Play.noteOn(): Invalid pitchbend {bend}, expected pitchbend in range {OUR_PITCHBEND_MIN} to {OUR_PITCHBEND_MAX}. Perhaps reset global pitch bend via Play.setPitchBend(0)... ?'
         print(error_msg)

   @staticmethod
   def noteOff(pitch, channel=0):
      """Stop a pitch from sounding.

      If the pitch is not sounding on this channel, nothing happens.

      Args:
          pitch (int or float): A MIDI pitch from 0 to 127, or a frequency in hertz (8.17 to 12600.0).
          channel (int, optional): The channel it is playing on, from 0 to 15.
      """
      if (isinstance(pitch, float)) and (8.17 <= pitch <= 12600.0): # a frequency in Hertz (within MIDI pitch range 0 to 127)?
         pitch, bend = freqToNote(pitch) # convert to pitch

      if (isinstance(pitch, int)) and (0 <= pitch <= 127):   # a MIDI pitch?

         # keep track of how many overlapping instances of this frequency are currently playing on this channel
         # so that we turn off only the last one - also see frequencyOn()
         noteID = (pitch, channel)                   # create an ID using pitch-channel pair

         try:
            # next, remove this noteID from the list, so that we may check for remaining instances
            _notesCurrentlyPlaying.remove(noteID)

            # and turn off the note
            _MIDI_SYNTH.noteoff(channel, pitch)

         except:
            # note not playing, so do nothing
            pass
            # print("Play: Warning - tried to turn off a note/frequency that wasn't playing.")

      else:
         print(f'Play.noteOff(): Unrecognized pitch {pitch}, expected MIDI pitch from 0 to 127 (int), or frequency in Hz from 8.17 to 12600.0 (float).')

   @staticmethod
   def frequencyOff(frequency, channel=0):
      """Stop a frequency from sounding.

      If the frequency is not sounding on this channel, nothing happens.

      Args:
          frequency (float): The frequency to stop, in hertz (8.17 to 12600.0).
          channel (int, optional): The channel it is playing on, from 0 to 15.
      """
      if (isinstance(frequency, float)) and (8.17 <= frequency <= 12600.0): # a frequency in Hertz (within MIDI pitch range 0 to 127)?

         pitch, bend = freqToNote( frequency )                     # convert to MIDI note and pitch bend
         Play.noteOff(pitch, channel)

      else:     # frequency was outside expected range
         print(f'Play.frequencyOff(): Invalid frequency {frequency}, expected frequency in Hz from 8.17 to 12600.0 (float).')

   @staticmethod
   def note(pitch, start, duration, velocity=100, channel=0, panning=-1):
      """Schedule a note to play after a delay and last a set time.

      Args:
          pitch (int or float): A MIDI pitch from 0 to 127, or a frequency in hertz (8.17 to 12600.0) to reach pitches between the standard notes.
          start (int or float): How long from now the note begins, in milliseconds.
          duration (int or float): How long the note lasts, in milliseconds.
          velocity (int, optional): How loud the note is, from 0 to 127.
          channel (int, optional): The channel to play on, from 0 to 15.
          panning (int, optional): Stereo position from 0 (left) to 127 (right); -1 uses the global panning.
      """
      # TODO: We should probably test for negative start times and durations.

      # create a timer for the note-on event
      noteOn = Timer(start, Play.noteOn, [pitch, velocity, channel, panning], False)

      # create a timer for the note-off event
      noteOff = Timer(start+duration, Play.noteOff, [pitch, channel], False)

      # add timers to WeakSets so allNotesOff() can manage them appropriately
      # WeakSet automatically removes completed timers to prevent memory leaks
      _noteOnTimers.add(noteOn)
      _noteOffTimers.add(noteOff)

      # store note information with the note-off timer so we only stop active notes in allNotesOff()
      # calculate absolute start time (start is relative to now)
      absoluteStartTime = time.time() * 1000 + start
      _noteOffTimerInfo[noteOff] = {'pitch': pitch, 'channel': channel, 'startTime': absoluteStartTime}

      # and activate timers (set things in motion)
      noteOn.start()
      noteOff.start()

      # NOTE:  Upon completion of this function, the two Timer objects become unreferenced.
      #        When the timers elapse, then the two objects (in theory) should be garbage-collectable,
      #        and should be eventually cleaned up.  So, here, no effort is made in reusing timer objects, etc.

   @staticmethod
   def frequency(frequency, start, duration, velocity=100, channel=0, panning=-1):
      """Schedule a frequency to play after a delay and last a set time.

      Play only one frequency per channel at a time: since this uses pitch bend, it affects
      every other note sounding on the channel.

      Args:
          frequency (float): The frequency to play, in hertz (8.17 to 12600.0).
          start (int or float): How long from now the note begins, in milliseconds.
          duration (int or float): How long the note lasts, in milliseconds.
          velocity (int, optional): How loud the note is, from 0 to 127.
          channel (int, optional): The channel to play on, from 0 to 15.
          panning (int, optional): Stereo position from 0 (left) to 127 (right); -1 uses the global panning.
      """
      # NOTE:  We assume that the end-user will ensure that concurrent microtones end up on
      # different channels.  This is needed since MIDI has only one pitch band per channel,
      # and most microtones require their unique pitch bending.

      # TODO: We should probably test for negative start times and durations.

      # create a timer for the frequency-on event
      frequencyOn = Timer(start, Play.frequencyOn, [frequency, velocity, channel, panning], False)

      # create a timer for the frequency-off event
      frequencyOff = Timer(start+duration, Play.frequencyOff, [frequency, channel], False)

      # call pitchBendNormal to turn off the timer, if it is on
      #setPitchBendNormal(channel)
      # and activate timers (set things in motion)
      frequencyOn.start()
      frequencyOff.start()


   # No (normal) pitch bend in JythonMusic (as opposed to MIDI) is 0, max downward bend is -8192, and max upward bend is 8191.
   # (Result is undefined if you exceed these values - it may wrap around or it may cap.)
   @staticmethod
   def setPitchBend(bend=0, channel=0):
      """Set the pitch bend for a channel, used for notes played next.

      Args:
          bend (int, optional): How far to bend the pitch, in pitch bend units from -8191 (full down) to 8192 (full up), where 0 means no bend.
          channel (int, optional): The channel to set, from 0 to 15.
      """
      if (bend <= OUR_PITCHBEND_MAX) and (bend >= OUR_PITCHBEND_MIN):   # is pitchbend within appropriate range?

         _currentPitchbend[channel] = bend        # remember the pitch bend (e.g., for Play.noteOn() )

         # TinySoundFont expects 0 to 16383 with 8192 (normal) as center
         tinysoundfontBend = bend + MIDI_PITCHBEND_NORMAL
         _MIDI_SYNTH.pitchbend(channel, tinysoundfontBend)  # set pitchbend on synthesizer

      else:     # frequency was outside expected range
         print(f'Play.setPitchBend(): Invalid pitchbend {bend}, expected pitchbend in range {OUR_PITCHBEND_MIN} to {OUR_PITCHBEND_MAX}.')

   @staticmethod
   def getPitchBend(channel=0):
      """Return the current pitch bend for a channel.

      Args:
          channel (int, optional): The channel to read, from 0 to 15.

      Returns:
          pitchBend (int): The current bend, in pitch bend units from -8191 to 8192, where 0 means no bend.
      """
      pitchBend = _currentPitchbend[channel]
      return pitchBend

   @staticmethod
   def allNotesOff():
      """Stop every note from sounding, on all channels.
      """
      global _MIDI_SYNTH, _notesCurrentlyPlaying, _noteOffTimers, _noteOffTimerInfo

      _MIDI_SYNTH.notes_off()          # on all channels by default
      _notesCurrentlyPlaying.clear()   # notes no longer playing

      # get current time in milliseconds (matching the timing used in Play.note())
      currentTime = time.time() * 1000

      # selectively stop note-off timers based on whether their notes have started
      timersToStop = []
      for timer in _noteOffTimers:
         if timer in _noteOffTimerInfo:
            noteInfo = _noteOffTimerInfo[timer]
            startTime = noteInfo['startTime']

            # only stop timers for notes that have already started playing
            # this preserves future scheduled notes while stopping sustained notes
            if startTime <= currentTime:
               timersToStop.append(timer)

      # stop the identified timers
      for timer in timersToStop:
         timer.stop()
         # remove from tracking (WeakKeyDictionary will auto-clean when timer is garbage collected)
         if timer in _noteOffTimerInfo:
            del _noteOffTimerInfo[timer]

         # remove from WeakSet
         if timer in _noteOffTimers:
            _noteOffTimers.discard(timer)

      # NOTE: We do NOT clear all _noteOffTimers or stop _noteOnTimers
      # This allows Play.midi or other scheduled notes to play (like JythonMusic)

   @staticmethod
   def allFrequenciesOff():
      """Stop every frequency from sounding, on all channels.

      Same as Play.allNotesOff(), and also resets pitch bend on every channel.
      """
      # Since frequencies are also represented as notes in MIDI,
      # we can reuse the allNotesOff implementation.
      Play.allNotesOff()

   @staticmethod
   def stop():
      """Stop all music started through Play from sounding.
      """
      # NOTE:  This could also handle Play.note() notes, which may have been
      #        scheduled to start sometime in the future.  For now, we assume that timer.py
      #        (which provides Timer objects) handles stopping of timers on its own.  If so,
      #        this takes care of our problem, for all practical purposes.  It is possible
      #        to have a race condition (i.e., a note that starts playing right when stop()
      #        is called, but a second call of stop() (e.g., double pressing of a stop button)
      #        will handle this, so we do not concern ourselves with it.

      # then, stop all sounding notes
      Play.allNotesOff()
      Play.allAudioNotesOff()

   @staticmethod
   def setInstrument(instrument, channel=0):
      """Set the instrument for a channel.

      Notes played on this channel will sound using this instrument.

      Args:
          instrument (int): The instrument (timbre), as a MIDI instrument number from 0 to 127.
          channel (int, optional): The channel to set, from 0 to 15.
      """
      _currentInstrument[channel] = instrument     # remember instrument
      if channel == 9:   # special handling for percussion channel
         if _SOUNDFONT_ID is not None:
            _MIDI_SYNTH.program_select(channel, _SOUNDFONT_ID, 0, instrument, is_drums=True)
      else:
         _MIDI_SYNTH.program_change(channel, instrument)  # set instrument on synthesizer

   @staticmethod
   def getInstrument(channel=0):
      """Return the instrument set for a channel.

      Args:
          channel (int, optional): The channel to read, from 0 to 15.

      Returns:
          instrument (int): The instrument (timbre), as a MIDI instrument number from 0 to 127.
      """
      instrument = _currentInstrument[channel]
      return instrument

   @staticmethod
   def setVolume(volume, channel=0):
      """Set the main volume for a channel.

      This is the channel's overall volume, separate from how loud each note is played
      (see Play.noteOn()).

      Args:
          volume (int): The main volume, from 0 to 127.
          channel (int, optional): The channel to set, from 0 to 15.
      """
      _currentVolume[channel] = volume     # remember volume
      _MIDI_SYNTH.control_change(channel, 7, volume)  # set volume on synthesizer

   @staticmethod
   def getVolume(channel=0):
      """Return the main volume for a channel.

      Args:
          channel (int, optional): The channel to read, from 0 to 15.

      Returns:
          volume (int): The main volume, from 0 to 127.
      """
      volume = _currentVolume[channel]
      return volume

   @staticmethod
   def setPanning(panning, channel=0):
      """Set the main stereo position for a channel.

      The default is the middle (64). Note that this does not affect a score played through
      Play.midi() or Play.audio().

      Args:
          panning (int): Stereo position from 0 (left) through 64 (center) to 127 (right).
          channel (int, optional): The channel to set, from 0 to 15.
      """
      # ensure panning is an int between 0 and 127
      if not (isinstance(panning, int) and 0 <= panning <= 127):
         print(f"Play.setPanning: Warning - Invalid panning value {panning}. Must be an integer between 0 and 127. No change.")

      else:
         _currentPanning[channel] = panning     # remember panning
         _MIDI_SYNTH.control_change(channel, 10, panning)   # set panning on synthesizer

   @staticmethod
   def getPanning(channel=0):
      """Return the main stereo position for a channel.

      Args:
          channel (int, optional): The channel to read, from 0 to 15.

      Returns:
          panning (int): Stereo position from 0 (left) through 64 (center) to 127 (right).
      """
      panning = _currentPanning[channel]
      return panning

   @staticmethod
   def audio(material, audioSamples, loopFlags=[], envelopes=[]):
      """Play music library material using audio samples as the instruments.

      Each channel in the material is played by the audio sample at the same position in
      audioSamples. The optional loopFlags and envelopes lists are parallel to
      audioSamples.

      Args:
          material (Note, Phrase, Part, or Score): The music to play.
          audioSamples (list[AudioSample]): The audio samples to play with, one per channel.
          loopFlags (list[bool], optional): Whether to loop each sample if a note outlasts it. Defaults to no looping.
          envelopes (list[Envelope], optional): An envelope to shape each sample's volume over time.
      """
      # ensure optional parameters have appropriate defaults
      if loopFlags == []:
         loopFlags = [False] * len(audioSamples)
      if envelopes == []:
         envelopes = [Envelope()] * len(audioSamples)

      # do necessary datatype wrapping (MidiSynth() expects a Score)
      if isinstance(material, Note):
         material = Phrase(material)
      if isinstance(material, Phrase):   # no elif - we need to successively wrap from Note to Score
         material = Part(material)
      if isinstance(material, Part):     # no elif - we need to successively wrap from Note to Score
         material = Score(material)
      if isinstance(material, Score):

         # we are good - let's play it then!

         score = material   # by now, material is a score, so create an alias (for readability)

         # loop through all parts and phrases to get all notes
         noteList = []               # holds all notes
         tempo = score.getTempo()    # get global tempo (can be overidden by part and phrase tempos)
         for part in score.getPartList():   # traverse all parts
            # NOTE: channel is used as an index for the audio voice
            channel = part.getChannel()        # get part channel
            instrument = part.getInstrument()  # get part instrument
            if part.getTempo() > -1:           # has the part tempo been set?
               tempo = part.getTempo()            # yes, so update tempo
            for phrase in part.getPhraseList():   # traverse all phrases in part
               if phrase.getInstrument() > -1:        # is this phrase's instrument set?
                  instrument = phrase.getInstrument()    # yes, so it takes precedence
               if phrase.getTempo() > -1:          # has the phrase tempo been set?
                  tempo = phrase.getTempo()           # yes, so update tempo

               # time factor to convert time from Score units to milliseconds
               # (this needs to happen here every time, as we may be using the tempo from score, part, or phrase)
               FACTOR = 1000 * 60.0 / tempo

               for index in range(phrase.getSize()):      # traverse all notes in this phrase
                  note = phrase.getNote(index)              # and extract needed note data
                  frequency = note.getFrequency()
                  panning = note.getPan()
                  panning = mapValue(panning, 0.0, 1.0, 0, 127)    # map from range 0.0..1.0 (Note panning) to range 0..127 (as expected by Java synthesizer)
                  start = int(phrase.getNoteStartTime(index) * FACTOR)  # get time and convert to milliseconds

                  # NOTE:  Below we use note length as opposed to duration (getLength() vs. getDuration())
                  # since note length gives us a more natural sounding note (with proper decay), whereas
                  # note duration captures the more formal (printed score) duration (which sounds unnatural).
                  duration = int(note.getLength() * FACTOR)   # convert to milliseconds
                  velocity = note.getDynamic()

                  # accumulate non-REST notes
                  if (frequency != REST):
                     noteList.append((start, duration, frequency, velocity, channel, instrument, panning))   # put start time first and duration second, so we can sort easily by start time (below),
                     # and so that notes that are members of a chord as denoted by having a duration of 0 come before the note that gives the specified chord duration

         # sort notes by start time
         noteList.sort()

         # Schedule playing all notes in noteList
         chordNotes = []      # used to process notes belonging in a chord
         for start, duration, pitch, velocity, channel, instrument, panning in noteList:
            # *** not needed, since we are using audio to play back music (was: set appropriate instrument for this channel)
            #Play.setInstrument(instrument, channel)

            # handle chord (if any)
            # Chords are denoted by a sequence of notes having the same start time and 0 duration (except the last note
            # of the chord).
            if duration == 0:   # does this note belong in a chord?
               chordNotes.append([start, duration, pitch, velocity, channel, panning])  # add it to the list of chord notes

            elif chordNotes == []:   # is this a regular, solo note (not part of a chord)?

               # yes, so schedule it to play via a Play.audioNote event
               Play.audioNote(pitch, start, duration, audioSamples[channel], velocity, panning, loopFlags[channel], envelopes[channel])

            else:   # note has a normal duration and it is part of a chord

               # first, add this note together with this other chord notes
               chordNotes.append([start, duration, pitch, velocity, channel, panning])

               # now, schedule all notes in the chord list using last note's duration
               for start, ignoreThisDuration, pitch, velocity, channel, panning in chordNotes:

                  # schedule this note using chord's duration (provided by the last note in the chord)
                  Play.audioNote(pitch, start, duration, audioSamples[channel], velocity, panning, loopFlags[channel], envelopes[channel])

               # now, all chord notes have been scheduled

               # so, clear chord notes to continue handling new notes (if any)
               chordNotes = []

         # now, all notes have been scheduled for future playing - scheduled notes can always be stopped using
         # JEM's stop button - this will stop all running timers (used by Play.note() to schedule playing of notes)
         #print "Play.note(" + str(pitch) + ", " + str(int(start * FACTOR)) + ", " + str(int(duration * FACTOR)) + ", " + str(velocity) + ", " + str(channel) + ")"

      else:   # error check
         print(f"Play.audio(): Unrecognized type {type(material)}, expected Note, Phrase, Part, or Score.")

   @staticmethod
   def audioNote(pitch, start, duration, audioSample, velocity=127, panning=-1, loopAudioSample=False, envelope=None):
      """Schedule a note to play with an audio sample, after a delay and lasting a set time.

      Args:
          pitch (int or float): A MIDI pitch from 0 to 127, or a frequency in hertz (8.17 to 12600.0).
          start (int or float): How long from now the note begins, in milliseconds.
          duration (int or float): How long the note lasts, in milliseconds.
          audioSample (AudioSample): The audio sample to play the note with.
          velocity (int, optional): How loud the note is, from 0 to 127.
          panning (int, optional): Stereo position from 0 (left) to 127 (right); -1 uses the global panning.
          loopAudioSample (bool, optional): Whether to loop the sample if the note outlasts it.
          envelope (Envelope, optional): An envelope to shape the note's volume over time.
      """
      # *** do more testing here

      if isinstance(pitch, int) and (0 <= pitch <= 127):   # a MIDI pitch?
         # yes, so convert pitch from MIDI number (int) to Hertz (float)
         pitch = noteToFreq(pitch)

      # create timers for note-on and note-off events
      audioOn  = Timer(start, Play.audioOn, [pitch, audioSample, velocity, panning, loopAudioSample, envelope], False)
      audioOff = Timer(start + duration, Play.audioOff, [pitch, audioSample, envelope], False)

      # everything is ready, so start timers to schedule playing of note
      audioOn.start()
      audioOff.start()


   #def audioOn(pitch, audioSample, velocity = 127, panning = -1, envelope = None, loopAudioSample = False):   #***
   @staticmethod
   def audioOn(pitch, audioSample, velocity=127, panning=-1, loopAudioSample=False, envelope=None):
      """Start a pitch sounding with an audio sample, and leave it sounding.

      Stop it with Play.audioOff().

      Args:
          pitch (int or float): A MIDI pitch from 0 to 127, or a frequency in hertz (8.17 to 12600.0).
          audioSample (AudioSample): The audio sample to play the pitch with.
          velocity (int, optional): How loud the note is, from 0 to 127.
          panning (int, optional): Stereo position from 0 (left) to 127 (right); -1 uses the global panning.
          loopAudioSample (bool, optional): Whether to loop the sample if it is shorter than the note.
          envelope (Envelope, optional): An envelope to shape the note's volume over time.
      """
      if isinstance(pitch, int) and (0 <= pitch <= 127):   # a MIDI pitch?
         # yes, so convert pitch from MIDI number (int) to Hertz (float)
         pitch = noteToFreq(pitch)

      if isinstance(pitch, float):        # a pitch in Hertz?

         # all good, so play it

         # allocate a AudioSample voice to play this pitch
         voice = audioSample._allocateVoiceForPitch(pitch)

         if voice is None:   # is there an available voice?

            print(f"Play.audioOn(): AudioSample does not have enough free voices to play this pitch, {pitch}.")

         else:   # we have a voice to play this pitch, so do it!!!

            # let's start the sound

            if panning != -1:                              # if we have a specific panning...
               audioSample.setPanning(panning, voice)         # then, use it (otherwise let default / global panning stand
            else:                                          # otherwise...
               audioSample.setPanning( Play.getPanning(), voice )   # use the global / default panning

            audioSample.setFrequency(pitch, voice)         # set the sample to the specified frequency

            if envelope:   # do we have an envelope to apply?

               # schedule volume changes needed to apply this envelope
               envelope.performAttackDelaySustain(audioSample, velocity, voice)

            else:   # no envelope, so...

               # set volume right away, as specified
               audioSample.setVolume(volume = velocity, voice = voice)         # and specified volume

            # ready - let make some sound!!!
            if loopAudioSample:

               audioSample.loop(start=0, size=-1, voice=voice)   # loop it continuously (until the end of the note)

            else:

               audioSample.play(start=0, size=-1, voice=voice)   # play it just once, and stop (even if before the end of the note)

      else:

         print(f"Play.audioNoteOn(): Unrecognized pitch {pitch}, expected MIDI pitch from 0 to 127 (int), or frequency in Hz from 8.17 to 12600.0 (float).")

   @staticmethod
   def audioOff(pitch, audioSample, envelope=None):
      """Stop a pitch from sounding on an audio sample.

      If the pitch is not sounding on this sample, nothing happens.

      Args:
          pitch (int or float): A MIDI pitch from 0 to 127, or a frequency in hertz (8.17 to 12600.0).
          audioSample (AudioSample): The audio sample the pitch is playing on.
          envelope (Envelope, optional): The same envelope passed to the matching Play.audioOn(), so its release can be applied.
      """
      if isinstance(pitch, int) and (0 <= pitch <= 127):   # a MIDI pitch?
         # yes, so convert pitch from MIDI number (int) to Hertz (float)
         pitch = noteToFreq(pitch)

      if isinstance(pitch, float):        # a pitch in Hertz?

         # all good, so stop it

         voice = audioSample._getVoiceForPitch(pitch)   # find which voice is being used to play this pitch

         if voice is not None:   # if a voice was associated with this pitch (as opposed to None) - meaning that this pitch was sounding...

            if envelope:   # if there is an envelope to apply...

               # release sound and stop, as prescribed by this envelope
               envelope.performReleaseAndStop(audioSample, voice)

            else:   # no envelope, so...

               # stop sound right away
               audioSample.stop(voice)

            # now, return the voice back to the pool of free voices (to potentially be used to play other notes)
            audioSample._deallocateVoiceForPitch(pitch)

         #else:
         #
         #  Could output a warning that this pitch is not playing, but let's be silent - better for live coding performances...
         #

      else:
         print(f"Play.audioNoteOff(): Unrecognized pitch {pitch}, expected MIDI pitch from 0 to 127 (int), or frequency in Hz from 8.17 to 12600.0 (float).")

   @staticmethod
   def allAudioNotesOff():
      """Stop every note from sounding on all audio samples.
      """
      # stop all notes from all active AudioSamples
      for a in _activeAudioSamples:

         # stop all voices for this AudioSample
         for voice in range(a.maxVoices):
            a.stop(voice)    # no need to check if they are playing - just do it (it's fine)

      # NOTE: One possibility here would be to also handle scheduled notes through Play.audio().  This could be done
      # by creating a list of AudioSamples and Timers created via audioNote() and looping through them to stop them.
      # For now, it makes sense to keep separate Play.audio() activity (which is score based), and Live Coding activity
      # i.e., interactively playing AudioSamples.

   @staticmethod
   def code(material, actions):
      """Run your own functions in time with music library material.

      Instead of making sound, each note triggers a function. The note's channel chooses
      which function in actions to call, so actions needs one function per channel used.

      Args:
          material (Note, Phrase, Part, or Score): The music whose notes drive the timing.
          actions (list[Callable]): The functions to call, one per channel.
      """
      # do necessary datatype wrapping (MidiSynth() expects a Score)
      if isinstance(material, Note):
         material = Phrase(material)
      if isinstance(material, Phrase):   # no elif - we need to successively wrap from Note to Score
         material = Part(material)
         material.setInstrument(-1)     # indicate no default instrument (needed to access global instrument)
      if isinstance(material, Part):     # no elif - we need to successively wrap from Note to Score
         material = Score(material)
      if isinstance(material, Score):
         # we are good - let's play it then!

         score = material   # by now, material is a score, so create an alias (for readability)

         # loop through all parts and phrases to get all notes
         noteList = []               # holds all notes
         tempo = score.getTempo()    # get global tempo (can be overidden by part and phrase tempos)
         for part in score.getPartList():   # traverse all parts
            channel = part.getChannel()        # get part channel
            instrument = Play.getInstrument(channel)  # get global instrument for this channel
            if part.getInstrument() > -1:      # has the part instrument been set?
               instrument = part.getInstrument()  # yes, so it takes precedence
            if part.getTempo() > -1:           # has the part tempo been set?
               tempo = part.getTempo()            # yes, so update tempo
            for phrase in part.getPhraseList():   # traverse all phrases in part
               if phrase.getInstrument() > -1:        # is this phrase's instrument set?
                  instrument = phrase.getInstrument()    # yes, so it takes precedence
               if phrase.getTempo() > -1:          # has the phrase tempo been set?
                  tempo = phrase.getTempo()           # yes, so update tempo

               # time factor to convert time from Score units to milliseconds
               # (this needs to happen here every time, as we may be using the tempo from score, part, or phrase)
               FACTOR = 1000 * 60.0 / tempo

               for index in range(phrase.getSize()):      # traverse all notes in this phrase
                  note = phrase.getNote(index)              # and extract needed note data
                  frequency = note.getFrequency()
                  panning = note.getPan()
                  panning = mapValue(panning, 0.0, 1.0, 0, 127)    # map from range 0.0..1.0 (Note panning) to range 0..127 (as expected by Java synthesizer)
                  start = int(phrase.getNoteStartTime(index) * FACTOR)  # get time and convert to milliseconds

                  # NOTE:  Below we use note length as opposed to duration (getLength() vs. getDuration())
                  # since note length gives us a more natural sounding note (with proper decay), whereas
                  # note duration captures the more formal (printed score) duration (which sounds unnatural).
                  duration = int(note.getLength() * FACTOR)   # convert to milliseconds
                  velocity = note.getDynamic()

                  # accumulate non-REST notes
                  # if (frequency != REST):
                  #    noteList.append((start, duration, frequency, velocity, channel, instrument, panning))   # put start time first and duration second, so we can sort easily by start time (below),
                     # and so that notes that are members of a chord as denoted by having a duration of 0 come before the note that gives the specified chord duration

                  # since they may want to give special meaning to REST notes, accumulate all notes (including RESTs)
                  # NOTE:  This is different from play.midi() and play.audio()
                  noteList.append((start, duration, frequency, velocity, channel, instrument, panning))   # put start time first and duration second, so we can sort easily by start time (below),

         # sort notes by start time
         noteList.sort()

         # schedule playing all notes in noteList
         chordNotes = []      # used to process notes belonging in a chord
         for start, duration, frequency, velocity, channel, instrument, panning in noteList:
            # set appropriate instrument for this channel
            #Play.setInstrument(instrument, channel)

            # handle chord (if any)
            # Chords are denoted by a sequence of notes having the same start time and 0 duration (except the last note
            # of the chord).
            if duration == 0:   # does this note belong in a chord?
               chordNotes.append([start, duration, frequency, velocity, channel, instrument, panning])  # add it to the list of chord notes

            elif chordNotes == []:   # is this a regular, solo note (not part of a chord)?

               # yes, so schedule to execute the corresponding action for this note

               # extract action associated with this channel
               if len(actions) > channel:   # is there a action associated with this channel?

                  # create timer to call this action
                  action = actions[channel]
                  actionTimer = Timer(start, action, [frequency, start, duration, velocity, channel, instrument, panning], False)
                  actionTimer.start()

               else:   # no, there isn't, so let them know

                  print(f"Play.code(): No action provided for channel {channel}.")

               #print "Play.note(" + str(frequency) + ", " + str(int(start * FACTOR)) + ", " + str(int(duration * FACTOR)) + ", " + str(velocity) + ", " + str(channel) + ")"

            else:   # note has a normal duration and it is part of a chord

               # first, add this note together with this other chord notes
               chordNotes.append([start, duration, frequency, velocity, channel, instrument, panning])

               # now, schedule all notes in the chord list using last note's duration
               for start, ignoreThisDuration, frequency, velocity, channel, instrument, panning in chordNotes:
                  # schedule to execute the corresponding action for this note

                  # extract action associated with this channel
                  if len(actions) > channel:   # is there a action associated with this channel?

                     # create timer to call this action
                     action = actions[channel]
                     actionTimer = Timer(start, action, [frequency, start, duration, velocity, channel, instrument, panning], False)
                     actionTimer.start()

                  else:   # no, there isn't, so let them know
                     print(f"Play.code(): No action provided for channel {channel}.")

               # now, all chord notes have been scheduled

               # so, clear chord notes to continue handling new notes (if any)
               chordNotes = []

         # now, all notes have been scheduled for future playing - scheduled notes can always be stopped using
         # JEM's stop button - this will stop all running timers

      else:   # error check
         print(f"Play.code(): Unrecognized type {type(material)}, expected Note, Phrase, Part, or Score.")

   @staticmethod
   def getSoundfont():
      """Return the path of the soundfont currently used for playback.

      Returns:
          soundfontPath (str): The file path of the current soundfont.
      """
      soundfontPath = _SOUNDFONT_PATH
      return soundfontPath

   @staticmethod
   def setSoundfont(soundfont):
      """Set the soundfont used for playback.

      A soundfont supplies the instrument sounds the synthesizer plays.

      Args:
          soundfont (str): The file path of the soundfont to use.
      """
      from pathlib import Path
      global _SOUNDFONT_ID

      soundfontPath = Path(soundfont)

      if not soundfontPath.exists():
         print(f"Play.setSoundfont(): Failed to find soundfont {soundfont}")
      else:
         try:
            if _SOUNDFONT_ID is not None:  # unload existing soundfont, if any
               _MIDI_SYNTH.sfunload(_SOUNDFONT_ID)

            # load soundfont file
            # DECIBEL_REDUCTION = -1.0
            # _SOUNDFONT_ID = _MIDI_SYNTH.sfload(soundfont, DECIBEL_REDUCTION)
            _SOUNDFONT_ID = _MIDI_SYNTH.sfload(soundfont)

         except Exception as e:
            # error, so warn the user
            print(f'Play.setSoundfont(): Error setting up MIDI synthesizer (after soundfont load attempt): {e}')
         else:
            # loaded successfully
            # so, set the soundfont for all 16 channels of the midi synth
            try:
               for i in range(16):   # for all 16 channels
                  if i == 9:   # reserve channel 9 for percussion
                     _MIDI_SYNTH.program_select(i, _SOUNDFONT_ID, 0, 0, is_drums=True)
                  else:   # non-percussion channel
                     _MIDI_SYNTH.program_select(i, _SOUNDFONT_ID, 0, 0, is_drums=False)
               # now, all 16 channels are set

            except Exception as e:   # soundfont not set for each channel
               # so, warn the user
               print(f'Play.setSoundfont(): Error setting soundfont for MIDI synthesizer channels: {e}')

   @staticmethod
   def _cleanupOldNotes():
      """"""
      global _notesCurrentlyPlaying

      if len(_notesCurrentlyPlaying) > _MAX_NOTES_ON:

         print("music: Warning - maximum number of notes on reached (255)."
               "\nPlay.note/frequencyOn() should eventually be accompanied by "
               "Play.note/frequencyOff(). \nOtherwise, consider using Play.note/frequency().\n")

         # calculate how many notes to remove (keep only the most recent ones)
         notesToRemove = len(_notesCurrentlyPlaying) - int(_MAX_NOTES_ON * 0.75)   # keep 75% of max

         # remove the oldest notes (first in the list)
         for _ in range(min(notesToRemove, len(_notesCurrentlyPlaying))):

            if _notesCurrentlyPlaying:
               pitch, channel = _notesCurrentlyPlaying.pop(0)   # remove oldest note
               _MIDI_SYNTH.noteoff(channel, pitch)             # actually turn it off

      # print(f"Note cleanup: Removed {notesToRemove} old notes to prevent accumulation")


#######################################################################################
# Soundfont
#######################################################################################

def _findSoundfont():
   """"""
   from pathlib import Path
   from platformdirs import user_data_dir  # system-specific application cache
   import sys
   import os

   candidates = []  # possible soundfont locations, in order of priority

   # path environment variable
   soundfontEnv = os.getenv("CREATIVEPYTHON_SOUNDFONT")
   if soundfontEnv is not None:
      candidates.append(Path(soundfontEnv))

   # local locations
   candidates.append(Path.cwd())                  # where user's script is running from       ('.')
   candidates.append(Path.cwd() / "Soundfonts")   # a local folder for soundfonts             ('./Soundfonts')
   candidates.append(Path.cwd() / "soundfonts")   #                                           ('./soundfonts')
   candidates.append(Path.home() / "Soundfonts")  # standard folder in user's home directory  ('~/Soundfonts')
   candidates.append(Path.home() / "soundfonts")  #                                           ('~/soundfonts')

   # automatic download cache
   candidates.append(Path(user_data_dir("PythonMusic", "CofC")) / "Soundfonts")

   # bundled soundfont location (for PyInstaller)
   if hasattr(sys, "_MEIPASS"):  # are we running in PyInstaller?
      candidates.append((Path(getattr(sys, "_MEIPASS")) / "soundfonts"))


   # now, we have our candidates, so let's search them in order
   soundfont = None
   i = 0

   while soundfont is None and i < len(candidates):
      location = candidates[i]                                 # get the location to check
      soundfontsAtLocation = list((location).glob("*.sf2")) \
                           + list((location).glob("*.SF2"))    # get a list of .sf2 files
      if len(soundfontsAtLocation) > 0:                        # pick the first one, if any
         soundfont = soundfontsAtLocation[0]
      else:
         soundfont = None
      i = i + 1                                                # increment

   # if a soundfont wasn't found, ask to download one
   if soundfont is None:
      # we use input() here, because we don't know if music.py will be
      # running in PEN, another editor, or as part of a standalone executable
      # built by PEN.  We may need to look into a GUI option...
      answer = None
      while answer not in ("y", "n"):
         answer = input("PythonMusic needs a soundfont (.sf2) to play MIDI.\nDownload a default soundfont? [y/n]").strip().lower()
         if answer in ("y", "yes"):
            answer = "y"
         if answer in ("n", "no"):
            answer = "n"

      if answer == "y":
         print("-" * 40)
         # print("PythonMusic: Failed to find local soundfont.")
         print("PythonMusic: Downloading soundfont...")
         print("-" * 40)
         destination = Path(user_data_dir("PythonMusic", "CofC")) / "Soundfonts"
         soundfont   = _downloadSoundfont(destination)
         print("Done!")
         print(f"Downloaded soundfont to: {str(destination)}")
         print(f"PythonMusic will use this soundfont from now on.")
         print("-" * 40)

      else:
         print("-" * 40)
         print("PythonMusic: Failed to find local soundfont.")
         print("Please add a soundfont (.sf2) to your local folder, or run your program again to download a soundfont.")
         print("-" * 40)
         print("Exiting...")
         exit()

   return str(soundfont)


def _downloadSoundfont(destination):
   """"""
   from pooch import retrieve  # secure download helper
   SF2_URL    = "https://www.dropbox.com/s/xixtvox70lna6m2/FluidR3%20GM2-2.SF2?dl=1"
   SF2_SHA256 = "2ae766ab5c5deb6f7fffacd6316ec9f3699998cce821df3163e7b10a78a64066"
   destination.mkdir(parents=True, exist_ok=True)  # create destination, if it doesn't exist
   downloadPath = retrieve(                        # download soundfont
      url=SF2_URL,
      known_hash=f"sha256:{SF2_SHA256}",
      progressbar=False,  # quietly
      path=str(destination)
   )
   return downloadPath

#######################################################################################
# MIDI Synthesizer
#######################################################################################

_MIDI_SYNTH     = tinysoundfont.Synth()  # prepare synthesizer
_SOUNDFONT_PATH = _findSoundfont()       # find default soundfont location
_SOUNDFONT_ID   = None                   # tinysoundfont Soundfont ID (used to unload)
Play.setSoundfont(_SOUNDFONT_PATH)       # set the soundfont
_MIDI_SYNTH.start()                      # start the synthesizer

# register MIDI synthesizer cleanup function with atexit
# to ensure the synth stops when the program exits
atexit.register(_MIDI_SYNTH.stop)


#######################################################################################
##### Mod #############################################################################
#######################################################################################

class Mod():
   """Transform musical material: change its pitch, timing, dynamics, and more.

   Mod is a static utility. Call its methods on the class itself, for example
   Mod.transpose(). Each method changes the material you pass in directly (in place),
   rather than returning a new copy. Most methods accept a Phrase, Part, or Score; some
   also accept a single Note.
   """

   @staticmethod
   def accent(material, meter, accentedBeats=[0.0], accentAmount=20):
      """Make certain beats of each measure louder, in place.

      Args:
          material (Phrase, Part, or Score): The music to change.
          meter (int or float): The number of beats per measure, for example 4.0.
          accentedBeats (list[int or float], optional): Which beats to accent, in beats from the start of the measure.
          accentAmount (int, optional): How much louder to make the accented beats, from 0 to 127.
      """
      # accept a list of beats from the user, but use a set internally for membership checks
      accentedBeats = set(accentedBeats)

      # define helper functions
      def accentPhrase(phrase):
         """"""
         beatCounter = phrase.getStartTime()

         # for every note in phrase...
         for note in phrase.getNoteList():

            # check note against each accented beat
            for beat in accentedBeats:

               # if note occurs on accented beat, increase dynamic level
               if beatCounter % meter == beat:
                  tempDynamic = note.getDynamic() + accentAmount
                  note.setDynamic(tempDynamic)

            # update current beat count
            beatCounter += note.getDuration()

      def accentPart(part):
         """"""
         for phrase in part.getPhraseList():
            accentPhrase(phrase)

      def accentScore(score):
         """"""
         for part in score.getPartList():
            accentPart(part)

      # do some basic error checking
      if float(meter) <= 0.0:
         raise TypeError(f"Expected meter greater than 0.0 - (it was {meter}).")

      for accentedBeat in accentedBeats:
         if not 0.0 <= float(accentedBeat) < float(meter):
            raise ValueError(f"Expected accented beat between 0.0 and {meter} - (it was {accentedBeat}).")

      if type(material) is Score:
         accentScore(material)

      elif type(material) is Part:
         accentPart(material)

      elif type(material) is Phrase:
         accentPhrase(material)

      else:
         raise TypeError(f"Unrecognized material type {type(material)} - expected Phrase, Part, or Score.")

   @staticmethod
   def append(material1, material2):
      """Add the second material onto the end of the first, in place.

      Both materials must be the same kind. For two notes, the first note's duration is
      extended (its pitch is unchanged).

      Args:
          material1 (Note, Phrase, Part, or Score): The material to add onto; this one is changed.
          material2 (Note, Phrase, Part, or Score): The material to append.
      """
      if type(material1) is Note and type(material2) is Note:
         material1.setDuration(material1.getDuration() + material2.getDuration())

      elif type(material1) is Phrase and type(material2) is Phrase:
         for note in material2.getNoteList():
            material1.addNote(note.copy())

      elif type(material1) is Part and type(material2) is Part:
         for phrase in material2.getPhraseList():
            material1.addPhrase(phrase.copy())

      elif type(material1) is Score and type(material2) is Score:
         endTime = material1.getEndTime()

         for part in material2.copy().getPartList():
            for phrase in part.getPhraseList():
               if phrase.getNoteList():
                  phrase.setStartTime(phrase.getStartTime() + endTime)
                  phrase.setInstrument(-1)

            material1.addPart(part)

      else:
         raise TypeError(f"Expected arguments of the same type - (it was {type(material1)} and {type(material2)})")

   @staticmethod
   def bounce(material):
      """Pan notes hard left and right, alternating from note to note, in place.

      Args:
          material (Phrase, Part, or Score): The music to change.
      """

      # define helper functions
      def bouncePhrase(phrase):
         """"""
         newPan = 0.0
         panIncrement = 1.0

         # for every note in phrase...
         for note in phrase.getNoteList():
            note.setPan(newPan)         # set panning
            newPan += panIncrement      # increment panning value
            panIncrement *= -1          # alternate panning increment

      def bouncePart(part):
         """"""
         for phrase in part.getPhraseList():
            bouncePhrase(phrase)

      def bounceScore(score):
         """"""
         for part in score.getPartList():
            bouncePart(part)

      if type(material) is Score:
         bounceScore(material)

      elif type(material) is Part:
         bouncePart(material)

      elif type(material) is Phrase:
         bouncePhrase(material)

      else:
         raise TypeError(f"Unrecognized material type {type(material)} - expected Phrase, Part, or Score.")

   @staticmethod
   def changeLength(phrase, newLength):
      """Stretch or squeeze a phrase so it lasts a set number of beats, in place.

      Like Mod.elongate(), but you give the final length rather than a scaling factor.

      Args:
          phrase (Phrase): The phrase to change.
          newLength (int or float): The phrase's new total length, in beats.
      """
      # do some basic error checking
      if float(newLength) <= 0.0:
         raise TypeError(f"Expected newLength greater than 0.0 - (it was {newLength}).")

      if type(phrase) is not Phrase:
         raise TypeError(f"Unrecognized material type {type(phrase)} - expected Phrase.")

      oldLength = phrase.getEndTime() - phrase.getStartTime()
      Mod.elongate(phrase, newLength / oldLength)

   @staticmethod
   def compress(material, ratio):
      """Squeeze or stretch the loudness range of the notes, in place.

      Each note's loudness is moved toward or away from the average by the given ratio: 0
      makes every note the average loudness, 1 leaves it unchanged, and 2 makes every note
      twice as far from the average. Negative values flip notes to the other side of the
      average.

      Args:
          material (Note, Phrase, Part, or Score): The music to change.
          ratio (int or float): How much to squeeze (below 1) or stretch (above 1) the loudness range.
      """

      # define helper functions
      def compressNote(note, mean, ratio):
         """"""
         if not note.isRest():   # skip rests
            oldDynamic = note.getDynamic()   # get current dynamic
            newDynamic = round(mean + ((oldDynamic - mean) * ratio))   # calculate new dynamic

            # clamp to valid MIDI range [0, 127]
            newDynamic = max(0, min(127, newDynamic))
            note.setDynamic(newDynamic)

      def compressPhrase(phrase, mean, ratio):
         """"""
         # for every note in phrase...
         for note in phrase.getNoteList():
            compressNote(note, mean, ratio)   # compress the note

      def compressPart(part, mean, ratio):
         """"""
         # for every phrase in part...
         for phrase in part.getPhraseList():
            compressPhrase(phrase, mean, ratio)   # compress the phrase

      def compressScore(score, mean, ratio):
         """"""
         # for every part in score...
         for part in score.getPartList():
            compressPart(part, mean, ratio)   # compress the part

      # do some type checking
      if not isinstance(material, (Score, Part, Phrase, Note)):
         raise TypeError(f"Mod.compress(): material must be a Score, Part, Phrase, or Note - (it was {type(material)}).")

      if not isinstance(ratio, (int, float)):
         raise TypeError(f"Mod.compress(): ratio must be a number - (it was {type(ratio)}).")

      # calculate the mean dynamic of all non-rest notes in the material
      totalDynamics = 0   # sum of all dynamics
      noteCount = 0       # number of audible notes

      # get a note list based on the material type
      notesToProcess = []
      if isinstance(material, Note):   # Note
         notesToProcess = [material]

      elif isinstance(material, Phrase):   # Phrase
         notesToProcess = material.getNoteList()

      elif isinstance(material, Part):   # Part
         # for every phrase in part...
         for phrase in material.getPhraseList():
            notesToProcess.extend(phrase.getNoteList())   # add phrase's notes to list

      elif isinstance(material, Score):   # Score
         # for every part
         for part in material.getPartList():
            # for every phrase
            for phrase in part.getPhraseList():
               notesToProcess.extend(phrase.getNoteList())   # add phrase's notes to list

      # collect dynamics from notes
      for note in notesToProcess:
         if not note.isRest():   # audible note?
            totalDynamics += note.getDynamic()   # accumulate dynamic
            noteCount += 1                       # increment counter

      # only proceed if there are audible notes to calculate a mean from
      if noteCount > 0:
         mean = totalDynamics / noteCount   # calculate the global mean

         # apply compression/expansion based on material type
         if isinstance(material, Note):
            compressNote(material, mean, ratio)

         elif isinstance(material, Phrase):
            compressPhrase(material, mean, ratio)

         elif isinstance(material, Part):
            compressPart(material, mean, ratio)

         elif isinstance(material, Score):
            compressScore(material, mean, ratio)
      # now, the dynamic of every note has been adjusted

   @staticmethod
   def crescendo(material, startTime, endTime, startVolume, endVolume):
      """Slide the volume smoothly from one level to another over a span of time, in place.

      Use a rising volume for a crescendo or a falling one for a diminuendo.

      Args:
          material (Phrase, Part, or Score): The music to change.
          startTime (int or float): When the slide begins, in beats.
          endTime (int or float): When the slide ends, in beats.
          startVolume (int or float): The volume at the start, from 0 to 127.
          endVolume (int or float): The volume at the end, from 0 to 127.
      """
      for name, val in [("startTime", startTime), ("endTime", endTime),
                        ("startVolume", startVolume), ("endVolume", endVolume)]:
         if type(val) not in [int, float]:
            raise TypeError(f"Unrecognized {name} type {type(val)} - expected int or float.")

      if startTime >= endTime:
         raise ValueError(f"startTime ({startTime}) must be less than endTime ({endTime}).")

      if isinstance(material, Score):
         for part in material.getPartList():
            Mod.crescendo(part, startTime, endTime, startVolume, endVolume)

      elif isinstance(material, Part):
         for phrase in material.getPhraseList():
            Mod.crescendo(phrase, startTime, endTime, startVolume, endVolume)

      elif isinstance(material, Phrase):
         durationCounter = material.getStartTime()
         for note in material.getNoteList():
            if startTime <= durationCounter < endTime:
               newVolume = mapValue(durationCounter, startTime, endTime, startVolume, endVolume)
               note.setDynamic(newVolume)
            durationCounter += note.getDuration()

      else:
         raise TypeError(f"Unrecognized material type {type(material)} - expected Phrase, Part, or Score.")

   @staticmethod
   def consolidate(part):
      """Merge all of a part's phrases into a single phrase, in place.

      Handy before View.notate(), which shows only one phrase at a time.

      Args:
          part (Part): The part to change.
      """
      # do some basic error checking
      if type(part) is not Part:
         raise TypeError(f"Unrecognized material type {type(part)} - expected Part.")

      part.__str__()

      prevsst = part.getStartTime()   # previous smallest start time (start of part)
      finished = False                # are we done consolidating?

      newPhrase = Phrase()

      while not finished:
         sst = float(np.inf)    # smallest start time (initialized to big number)
         tempPhrase = None

         # get phrase with earliest start time
         for phrase in part.getPhraseList():
            if phrase.getStartTime() < sst and phrase.getSize() > 0:
               tempPhrase = phrase
               sst = phrase.getStartTime()

         if tempPhrase is None:
            finished = True
            break

         note = tempPhrase.getNote(0)        # get next note from phrase

         if not note.isRest():

            if newPhrase.getSize() == 0:        # if this is the first note
               newPhrase.setStartTime(sst)

            else:                               # if this is not the first note
               newDuration = int(((sst - prevsst) * 100000) + 0.5) / 100000.0          # calculate new duration for previous note
               newPhrase.getNote(newPhrase.getSize() - 1).setDuration(newDuration)     # update previous note's duration

            newPhrase.addNote(note)

         tempPhrase.removeNote(0)    # remove note from phrase

         newStartTime = int(((sst + note.getDuration()) * 100000) + 0.5) / 100000.0      # calculate new start time for phrase
         tempPhrase.setStartTime(newStartTime)                                           # update phrase's start time

         prevsst = sst               # update previou smallest start time

      part.empty()
      part.addPhrase(newPhrase)

   @staticmethod
   def cycle(phrase, numberOfNotes):
      """Repeat a phrase until it holds a set number of notes, in place.

      Like Mod.repeat(), but the last repetition may be cut short once the note count is
      reached.

      Args:
          phrase (Phrase): The phrase to change.
          numberOfNotes (int): How many notes the phrase should end up with.
      """
      # do some basic error checking
      if type(phrase) is not Phrase:
         raise TypeError(f"Unrecognized material type {type(phrase)} - expected Phrase.")
      elif type(numberOfNotes) is not int:
         raise TypeError(f"Unexpected times type {type(numberOfNotes)} - expected int.")
      elif numberOfNotes <= phrase.getSize():
         raise ValueError("numberOfNotes should be greater than phrase size.")

      # for each additional note needed...
      for i in range(0, numberOfNotes - phrase.getSize()):

            noteCopy = phrase.getNote(i).copy()     # copy next note in sequence
            phrase.addNote(noteCopy)                # add note to end of phrase

   @staticmethod
   def elongate(material, scaleFactor):
      """Stretch or squeeze every note's length by a scaling factor, in place.

      A factor above 1.0 makes the music longer (slower); below 1.0 makes it shorter
      (faster). For example, 0.5 halves every duration.

      Args:
          material (Note, Phrase, Part, or Score): The music to change.
          scaleFactor (int or float): The factor to multiply every duration by.
      """
      # do some basic error checking
      if not isinstance(material, (Score, Part, Phrase, Note)):
         raise TypeError(f'Mod.elongate(): material must be a Score, Part, Phrase, or Note - (it was {type(material)}).')
      if not isinstance(scaleFactor, (int, float)):
         raise TypeError(f'Mod.elongate(): scaleFactor must be a number - (it was {type(scaleFactor)}).')
      if scaleFactor <= 0.0:
         raise ValueError(f'Mod.elongate(): scaleFactor must be greater than 0.0 - (it was {scaleFactor}).')

      # define helper functions
      def elongateNote(note, scaleFactor):
         note.setDuration(note.getDuration() * scaleFactor)  # elongate note

      def elongatePhrase(phrase, scaleFactor):
         for note in phrase.getNoteList():
            elongateNote(note, scaleFactor)

      def elongatePart(part, scaleFactor):
         for phrase in part.getPhraseList():
            elongatePhrase(phrase, scaleFactor)

      def elongateScore(score, scaleFactor):
         for part in score.getPartList():
            elongatePart(part, scaleFactor)

      # do the work
      if isinstance(material, Score):
         elongateScore(material, scaleFactor)
      elif isinstance(material, Part):
         elongatePart(material, scaleFactor)
      elif isinstance(material, Phrase):
         elongatePhrase(material, scaleFactor)
      elif isinstance(material, Note):
         elongateNote(material, scaleFactor)

   @staticmethod
   def fadeIn(material, fadeLength):
      """Fade the music up from silence to its normal volume, in place.

      Args:
          material (Phrase, Part, or Score): The music to change.
          fadeLength (int or float): How long the fade lasts, in beats.
      """
      if type(fadeLength) not in [float, int]:
         raise TypeError(f"Unrecognized fadeLength type {type(fadeLength)} - expected int or float.")

      if isinstance(material, Score):
         for part in material.getPartList():
            Mod.fadeIn(part, fadeLength)

      elif isinstance(material, Part):
         for phrase in material.getPhraseList():
            Mod.fadeIn(phrase, fadeLength)

      elif isinstance(material, Phrase):
         durationCounter = material.getStartTime()
         for note in material.getNoteList():
            fadeFactor = durationCounter / fadeLength
            if fadeFactor >= 1:
               break
            note.setDynamic(int(max(1, note.getDynamic() * fadeFactor)))
            durationCounter += note.getDuration()

      else:
         raise TypeError(f"Unrecognized material type {type(material)} - expected Phrase, Part, or Score.")

   @staticmethod
   def fadeOut(material, fadeLength, _endTime=None):
      """Fade the music down from its normal volume to silence, in place.

      Args:
          material (Phrase, Part, or Score): The music to change.
          fadeLength (int or float): How long the fade lasts, in beats.
          _endTime (int or float, optional): Internal use; leave unset.
      """
      if type(fadeLength) not in [float, int]:
         raise TypeError(f"Unrecognized fadeLength type {type(fadeLength)} - expected int or float.")

      if _endTime is None:
         _endTime = material.getEndTime()

      if isinstance(material, Score):
         for part in material.getPartList():
            Mod.fadeOut(part, fadeLength, _endTime)

      elif isinstance(material, Part):
         for phrase in material.getPhraseList():
            Mod.fadeOut(phrase, fadeLength, _endTime)

      elif isinstance(material, Phrase):
         durationCounter = material.getStartTime()
         for note in material.getNoteList():
            distFromEnd = _endTime - durationCounter
            if distFromEnd < fadeLength:
               fadeFactor = max(0, distFromEnd / fadeLength)
               note.setDynamic(int(max(1, note.getDynamic() * fadeFactor)))
            durationCounter += note.getDuration()

      else:
         raise TypeError(f"Unrecognized material type {type(material)} - expected Phrase, Part, or Score.")

   @staticmethod
   def fillRests(material):
      """Replace each note-then-rest with one longer note, in place.

      Lengthens a note to absorb the rest that follows it and removes the rest, lowering the
      note count.

      Args:
          material (Phrase, Part, or Score): The music to change.
      """

      # define helper functions
      def fillPhrase(phrase):
         """"""
         index = phrase.getSize() - 2
         while index > -1:
            currNote = phrase.getNote(index)
            nextNote = phrase.getNote(index + 1)

            if currNote.getPitch() != REST == nextNote.getPitch():

               newDuration = currNote.getDuration() + nextNote.getDuration()
               currNote.setDuration(newDuration)

               phrase.removeNote(index + 1)

               index -= 1

      def fillPart(part):
         """"""
         for phrase in part.getPhraseList():
               fillPhrase(phrase)

      def fillScore(score):
         """"""
         for part in score.getPartList():
            fillPart(part)

      # check type of material and call the appropriate function
      if isinstance(material, Score):
         fillScore(material)

      elif isinstance(material, Part):
         fillPart(material)

      elif isinstance(material, Phrase):
         fillPhrase(material)

      else:   # error check
         raise TypeError(f"Unrecognized material type {type(material)} - expected Phrase, Part, or Score.")

   @staticmethod
   def invert(phrase, pitchAxis, scale=CHROMATIC_SCALE, key=0):
      """Flip the pitches of a phrase around a center pitch, in place.

      A note that is some distance above the center pitch ends up the same distance below
      it, and vice versa. The order of the notes does not change.

      Args:
          phrase (Phrase): The phrase to change.
          pitchAxis (int): The center pitch to flip around, as a MIDI pitch.
          scale (list[int], optional): The scale to keep the flipped pitches in, a list of pitch classes between 0 and 11. If omitted, every pitch is allowed (the chromatic scale).
          key (int, optional): The scale's root pitch class, from 0 to 11, where 0 means C.
      """
      # do some basic error checking
      if type(pitchAxis) is not int:
         raise TypeError(f"Unrecognized pitchAxis type {type(pitchAxis)} - expected int.")
      if type(phrase) is not Phrase:
         raise TypeError(f"Unrecognized material type {type(phrase)} - expected Phrase.")

      # traverse list of notes, and adjust pitches accordingly
      smallestDuration = None

      for note in phrase.getNoteList():

         if not note.isRest():  # modify regular notes only (i.e., do not modify rests)
            invertedPitch = pitchAxis + (pitchAxis - note.getPitch())   # find mirror pitch around axis (by adding difference)
            note.setPitch(invertedPitch)                                # and update it

            if (smallestDuration is None) or (note.getDuration() < smallestDuration):
               # track the smallest non-REST duration in the phrase
               smallestDuration = note.getDuration()

      # now, all notes have been updated.  Next, quantize to filter into the given scale
      Mod.quantize(phrase, smallestDuration, scale, key)

   @staticmethod
   def merge(material1, material2):
      """Combine the second material into the first so they sound together, in place.

      Unlike Mod.append(), which places the second material after the first, this overlaps
      them in time. Both materials must be the same kind (Part or Score). Make sure their
      instruments and channels fit together.

      Args:
          material1 (Part or Score): The material to merge into; this one is changed.
          material2 (Part or Score): The material to merge in; this one is left unchanged.
      """
      # do some basic error checking
      if not isinstance(material1, (Part, Score)):
         raise TypeError(f"Mod.merge(): material1 must be a Part or Score - (it was {type(material1)}).")
      if type(material1) is not type(material2):
         raise TypeError(f"Mod.merge(): material1 and material2 must be the same type - (they were {type(material1)} and {type(material2)}).")

      # define helper functions
      def mergePart(part1, part2):
         """"""
         for phrase in part2.getPhraseList():
            part1.addPhrase(phrase.copy())  # copy() to avoid modifying original phrase in material2

      def mergeScore(score1, score2):
         for part in score2.getPartList():
            score1.addPart(part)

      # do the work
      if isinstance(material1, Score):
         mergeScore(material1, material2)
      elif isinstance(material1, Part):
         mergePart(material1, material2)

   @staticmethod
   def mutate(phrase):
      """Randomly change one note's pitch and one note's duration, in place.

      The new pitch is picked between the phrase's lowest and highest notes; the new
      duration is picked from those already in the phrase.

      Args:
          phrase (Phrase): The phrase to change.
      """
      import random

      # do some basic error checking
      if type(phrase) is not Phrase:
         raise TypeError("Unrecognized material type " + str(type(phrase)) + " - expected Phrase.")

      # pick random pitch between highest and lowest in phrase
      minPitch = int(phrase.getLowestPitch())
      maxPitch = int(phrase.getHighestPitch())
      newPitch = random.randint(minPitch, maxPitch)

      # pick random note in phrase to modify
      note = random.choice(phrase.getNoteList())

      # update pitch for selected note
      note.setPitch(newPitch)

      # pick random duration from phrase note
      durations = [note.getDuration() for note in phrase.getNoteList()]
      newDuration = random.choice(durations)

      # pick random note in phrase to modify
      note = random.choice(phrase.getNoteList())

      # update duration for selected note
      note.setDuration(newDuration)

   @staticmethod
   def normalize(material):
      """Scale every note's volume up so the loudest note reaches the maximum, in place.

      The notes keep their relative loudness.

      Args:
          material (Phrase, Part, or Score): The music to change.
      """
      maxDynamic = 0

      # check type of material and execute the appropriate code
      if isinstance(material, Score):

         for part in material.getPartList():
            for phrase in part.getPhraseList():
               for note in phrase.getNoteList():
                  maxDynamic = max(maxDynamic, note.getDynamic())

         diff = 127 - maxDynamic

         for part in material.getPartList():
            for phrase in part.getPhraseList():
               for note in phrase.getNoteList():
                  note.setDynamic(note.getDynamic() + diff)

      elif isinstance(material, Part):

         for phrase in material.getPhraseList():
            for note in phrase.getNoteList():
               maxDynamic = max(maxDynamic, note.getDynamic())

         diff = 127 - maxDynamic

         for phrase in material.getPhraseList():
            for note in phrase.getNoteList():
               note.setDynamic(note.getDynamic() + diff)

      elif isinstance(material, Phrase):

         for note in material.getNoteList():
            maxDynamic = max(maxDynamic, note.getDynamic())

         diff = 127 - maxDynamic

         for note in material.getNoteList():
            note.setDynamic(note.getDynamic() + diff)

      else:   # error check
         raise TypeError( "Unrecognized material type " + str(type(material)) + " - expected Phrase, Part, or Score." )

   @staticmethod
   def palindrome(material):
      """Double the music by adding a reversed copy of itself onto the end, in place.

      The result plays forward and then backward.

      Args:
          material (Phrase, Part, or Score): The music to change.
      """
      # check type of material
      if type(material) not in [Phrase, Part, Score]:
            raise TypeError("Unrecognized material type " + str(type(material)) + " - expected Phrase, Part, or Score.")

      # create copy of material to manipulate
      newMaterial = material.copy()

      # reverse new material and shift to end of material
      Mod.retrograde(newMaterial)
      Mod.shift(newMaterial, material.getStartTime())

      # merge new material into original material
      Mod.merge(material, newMaterial)

   @staticmethod
   def quantize(material, quantum, scale=CHROMATIC_SCALE, key=0):
      """Round note start times and durations to a grid, in place.

      Each note's start time and duration are rounded to the nearest multiple of quantum.
      A smaller quantum changes the music less; a larger one makes it sound more mechanical.
      If a scale is given, pitches are also snapped to it.

      Args:
          material (Note, Phrase, Part, or Score): The music to change.
          quantum (int or float): The grid size to round to, in beats.
          scale (list[int], optional): A scale to snap pitches to, a list of pitch classes between 0 and 11. If omitted, pitches are left alone.
          key (int, optional): The scale's root pitch class, from 0 to 11, where 0 means C.
      """
      # define helper functions
      def quantizeNote(note):
         """"""
         if note.getPitch() != REST:  # ignore rests
            # calculate new duration as a multiple of quantum
            newDuration = round(note.getDuration() / quantum) * quantum
            note.setDuration(newDuration)

            # coerce the pitch to a member of the scale, rooted at 'key'
            pitch           = note.getPitch()
            intervalFromKey = (pitch - key) % 12       # how far the note sits above the mode's root
            octaveRoot      = pitch - intervalFromKey  # the mode's root, in this note's octave
            i = len(scale) - 1

            while i >= 0:  # check each interval in scale, back to front
               scaleInterval = scale[i]
               if intervalFromKey >= scaleInterval:
                  # snap to the first (largest) scale interval it reaches
                  intervalFromKey = scaleInterval
                  i = -1  # break
               else:
                  i = i - 1

            # rebuild the pitch from the mode's root plus the snapped interval
            newPitch = octaveRoot + intervalFromKey
            note.setPitch(newPitch)

      def quantizePhrase(phrase):
         """"""
         for note in phrase.getNoteList():
               quantizeNote(note)

      def quantizePart(part):
         """"""
         for phrase in part.getPhraseList():
            quantizePhrase(phrase)

      def quantizeScore(score):
         """"""
         for part in score.getPartList():
            quantizePart(part)

      # check type of steps
      if type(quantum) not in (int, float):
         raise TypeError( "Unrecognized quantum type " + str(type(quantum)) + " - expected a number." )

      # a non-positive quantum has no meaningful subdivision, so leave the material unchanged
      if quantum <= 0:
         return

      # check type of material and execute the appropriate code
      if isinstance(material, Score):
         quantizeScore(material)

      elif isinstance(material, Part):
         quantizePart(material)

      elif isinstance(material, Phrase):
         quantizePhrase(material)

      elif isinstance(material, Note):
         quantizeNote(material)

      else:   # error check
         raise TypeError( "Unrecognized material type " + str(type(material)) + " - expected Note, Phrase, Part, or Score." )

   @staticmethod
   def randomize(material, pitchAmount, durationAmount=0, volumeAmount=0):
      """Nudge each note's pitch, duration, and volume by random amounts, in place.

      Each value changes by a random amount within plus or minus the amount you give. Set an
      amount to 0 to leave that property alone.

      Args:
          material (Note, Phrase, Part, or Score): The music to change.
          pitchAmount (int): The most each pitch may move, in semitones (keep results within 0 to 127).
          durationAmount (int or float, optional): The most each duration may move, in beats.
          volumeAmount (int, optional): The most each volume may move, from 0 to 127.
      """
      import random

      # do some basic error checking
      if not isinstance(material, (Note, Phrase, Part, Score)):
         raise TypeError(f'Mod.randomize(): material must be a Note, Phrase, Part, or Score (it was {type(material)})')
      elif not isinstance(pitchAmount, int):
         raise TypeError(f'Mod.randomize(): steps must be an integer (it was {type(pitchAmount)})')

      # support methods
      def randomizeNote(note):
         """"""
         if not note.isRest():  # rests aren't randomizable, so skip the work
            # pitch randomization
            if pitchAmount != 0:
               pitch = note.getPitch()
               pitchShift = random.randint(-pitchAmount, pitchAmount)
               newPitch = min(127, max(0, pitch + pitchShift))  # clamp to 0-127
               note.setPitch(newPitch)

            # duration randomization
            if durationAmount != 0:
               duration = note.getDuration()
               durationShift = random.uniform(-durationAmount, durationAmount)
               newDuration = max(0.01, duration + durationShift)  # don't allow negative durations
               note.setDuration(newDuration)

            # volume randomization
            if volumeAmount != 0:
               volume = note.getDynamic()
               volumeShift = random.randint(-volumeAmount, volumeAmount)
               newVolume = min(127, max(0, volume + volumeShift))  # clamp to 0-127
               note.setDynamic(newVolume)
      ### end randomizeNote()

      def randomizePhrase(phrase):
         for note in phrase.getNoteList():
            randomizeNote(note)

      def randomizePart(part):
         for phrase in part.getPhraseList():
            randomizePhrase(phrase)

      def randomizeScore(score):
         for part in score.getPartList():
            randomizePart(part)

      # time to actually do the work
      if isinstance(material, Score):
         randomizeScore(material)
      elif isinstance(material, Part):
         randomizePart(material)
      elif isinstance(material, Phrase):
         randomizePhrase(material)
      elif isinstance(material, Note):
         randomizeNote(material)

   @staticmethod
   def repeat(material, times):
      """Repeat the music a set number of times, in place.

      For example, Mod.repeat(phrase, 2) makes the phrase play twice.

      Args:
          material (Phrase, Part, or Score): The music to change.
          times (int): How many times the music should appear.
      """
      times = int(times)

      # check type of times
      if type(times) is not int:
         raise TypeError( "Unrecognized times type " + str(type(times)) + " - expected int." )

      # check type of material and execute the appropriate code
      if isinstance(material, Score):

         scoreCopy = material.copy()

         for i in range(times):

            newScore = scoreCopy.copy()

            Mod.shift(newScore, material.getEndTime())
            Mod.merge(material, newScore)

      elif isinstance(material, Part):
         partCopy = material.copy()

         for i in range(times):
            newPart = partCopy.copy()

            Mod.shift(newPart, material.getEndTime())
            Mod.merge(material, newPart)

      elif isinstance(material, Phrase):

         notes = material.copy().getNoteList()

         for i in range(times):
            for note in notes:
               material.addNote(note)

      else:   # error check
         raise TypeError( "Unrecognized material type " + str(type(material)) + " - expected Phrase, Part, or Score." )

   @staticmethod
   def retrograde(material):
      """Reverse the order of the notes, in place.

      Args:
          material (Phrase, Part, or Score): The music to change.
      """
      # do some basic error checking
      if not isinstance(material, (Phrase, Part, Score)):
         raise TypeError(f'Mod.retrograde(): material must be a Phrase, Part, or Score (it was {type(material)})')

      # define helper functions
      def retrogradePhrase(phrase):
         """"""
         noteList = phrase.copy().getNoteList()  # extract note list
         phrase.empty()                          # clear the phrase

         for note in noteList[::-1]:  # reverse the order of notes
            phrase.addNote(note)      # add them back in reverse order

      def retrogradePart(part):
         partEndTime   = part.getEndTime()

         for phrase in part.getPhraseList():
            retrogradePhrase(phrase)  # reverse the phrase
            # the retrograded phrase needs to start as far from the beginning of the part as
            # the original phrase was from the end of the part
            distanceFromEnd = partEndTime - (phrase.getStartTime() + phrase.getEndTime())
            Mod.shift(phrase, distanceFromEnd)

      def retrogradeScore(score):
         scoreEndTime   = score.getEndTime()

         for part in score.getPartList():
            retrogradePart(part)  # reverse the part
            # the retrograded part needs to start as far from the beginning of the score as
            # the original part was from the end of the score
            distanceFromEnd = scoreEndTime - (part.getStartTime() + part.getEndTime())
            Mod.shift(part, distanceFromEnd)


      # do the work
      if isinstance(material, Score):
         retrogradeScore(material)
      elif isinstance(material, Part):
         retrogradePart(material)
      elif isinstance(material, Phrase):
         retrogradePhrase(material)

   @staticmethod
   def rotate(phrase, times=1):
      """Shift the notes around the phrase, in place.

      Each shift moves the last note to the front, so the first note becomes the second, and
      so on.

      Args:
          phrase (Phrase): The phrase to change.
          times (int, optional): How many notes to shift by.
      """
      # do some basic error checking
      if type(phrase) is not Phrase:
         raise TypeError("Unrecognized material type " + str(type(phrase)) + " - expected Phrase.")
      elif type(times) is not int:
         raise TypeError("Unexpected times type " + str(type(phrase)) + " - expected int.")

      noteList = phrase.getNoteList()
      for i in range(times):
         lastNote = noteList.pop(-1)     # remove last note in phrase
         noteList.insert(0, lastNote)    # prepend it to front of noteList

   @staticmethod
   def shake(material, amount=20):
      """Randomly vary the notes' volumes for an uneven, human feel, in place.

      Args:
          material (Phrase, Part, or Score): The music to change.
          amount (int, optional): How strong the effect is. Each volume moves by up to this much, from 0 to 127.
      """
      import random

      # check type of amount
      if type(amount) is not int:
         raise TypeError( "Unrecognized time type " + str(type(amount)) + " - expected int." )

      # define helper functions
      def shakePhrase(phrase):
         """"""
         for note in phrase.getNoteList():

            newDynamic = note.getDynamic() + random.randint(-amount, amount)
            newDynamic = max(0, min(newDynamic, 127))

            note.setDynamic(newDynamic)

      def shakePart(part):
         """"""
         for phrase in part.getPhraseList():
            shakePhrase(phrase)

      def shakeScore(score):
         """"""
         for part in score.getPartList():
            shakePart(part)

      # check type of material and execute the appropriate code
      if isinstance(material, Score):
         shakeScore(material)

      elif isinstance(material, Part):
         shakePart(material)

      elif isinstance(material, Phrase):
         shakePhrase(material)

      else:   # error check
         raise TypeError( "Unrecognized material type " + str(type(material)) + " - expected Phrase, Part, or Score." )

   @staticmethod
   def shift(material, time):
      """Move every phrase's start time earlier or later, in place.

      A positive time moves the music later; a negative time moves it earlier, but not
      before the start of the piece (0.0).

      Args:
          material (Phrase, Part, or Score): The music to change.
          time (int or float): How far to move the music, in beats.
      """
      # do some basic error checking
      if not isinstance(material, (Phrase, Part, Score)):
         raise TypeError(f'Mod.shift(): material must be a Phrase, Part, or Score (it was {type(material)})')
      if not isinstance(time, (int, float)):
         raise TypeError(f'Mod.shift(): time must be a number (it was {type(time)})')

      # define helper functions
      def shiftPhrase(phrase, time):
         """"""
         newStartTime = phrase.getStartTime() + time
         newStartTime = max(0, newStartTime)  # don't allow negative start times
         phrase.setStartTime(newStartTime)

      def shiftPart(part, time):
         for phrase in part.getPhraseList():
            shiftPhrase(phrase, time)

      def shiftScore(score, time):
         for part in score.getPartList():
            shiftPart(part, time)

      # do the work
      if isinstance(material, Score):
         shiftScore(material, time)
      elif isinstance(material, Part):
         shiftPart(material, time)
      elif isinstance(material, Phrase):
         shiftPhrase(material, time)

   @staticmethod
   def shuffle(material):
      """Randomly reorder the notes, in place.

      Every note is kept; only their order changes.

      Args:
          material (Phrase, Part, or Score): The music to change.
      """
      import random

      # define helper functions
      def shufflePhrase(phrase):
         """"""
         random.shuffle(phrase.getNoteList())

      def shufflePart(part):
         """"""
         for phrase in part.getPhraseList():
            shufflePhrase(phrase)

      def shuffleScore(score):
         """"""
         for part in score.getPartList():
            shufflePart(part)

      # check type of material and execute the appropriate code
      if isinstance(material, Score):
         shuffleScore(material)

      elif isinstance(material, Part):
         shufflePart(material)

      elif isinstance(material, Phrase):
         shufflePhrase(material)

      else:   # error check
         raise TypeError( "Unrecognized material type " + str(type(material)) + " - expected Phrase, Part, or Score." )

   @staticmethod
   def spread(material):
      """Randomly pan the notes for an even spread across the stereo field, in place.

      Args:
          material (Phrase, Part, or Score): The music to change.
      """
      import random

      # define helper functions
      def spreadPhrase(phrase):
         """"""
         for note in phrase.getNoteList():
            note.setPan(random.random())

      def spreadPart(part):
         """"""
         for phrase in part.getPhraseList():
            spreadPhrase(phrase)

      def spreadScore(score):
         """"""
         for part in score.getPartList():
            spreadPart(part)

      # check type of material and execute the appropriate code
      if isinstance(material, Score):
         spreadScore(material)

      elif isinstance(material, Part):
         spreadPart(material)

      elif isinstance(material, Phrase):
         spreadPhrase(material)

      else:   # error check
         raise TypeError( "Unrecognized material type " + str(type(material)) + " - expected Phrase, Part, or Score." )

   @staticmethod
   def tiePitches(material):
      """Join neighboring notes of the same pitch into one longer note, in place.

      Like a musical tie. This lowers the note count.

      Args:
          material (Phrase, Part, or Score): The music to change.
      """

      # define helper functions
      def tiePhrase(phrase):
         """"""
         index = phrase.getSize() - 2
         while index > -1:

            currNote = phrase.getNote(index)
            nextNote = phrase.getNote(index + 1)

            if currNote.getPitch() == nextNote.getPitch():

               newDuration = currNote.getDuration() + nextNote.getDuration()
               currNote.setDuration(newDuration)

               phrase.removeNote(index + 1)

            index -= 1

      def tiePart(part):
         """"""
         for phrase in part.getPhraseList():
            tiePhrase(phrase)

      def tieScore(score):
         """"""
         for part in score.getPartList():
            tiePart(part)

      # check type of material and call the appropriate function
      if isinstance(material, Score):
         tieScore(material)

      elif isinstance(material, Part):
         tiePart(material)

      elif isinstance(material, Phrase):
         tiePhrase(material)

      else:   # error check
         raise TypeError( "Unrecognized material type " + str(type(material)) + " - expected Phrase, Part, or Score." )

   @staticmethod
   def tieRests(material):
      """Join neighboring rests into one longer rest, in place.

      This lowers the note count.

      Args:
          material (Phrase, Part, or Score): The music to change.
      """

      # define helper functions
      def tiePhrase(phrase):
         """"""
         index = phrase.getSize() - 2
         while index > -1:

               currNote = phrase.getNote(index)
               nextNote = phrase.getNote(index + 1)

               if currNote.getPitch() == nextNote.getPitch() == REST:

                  newDuration = currNote.getDuration() + nextNote.getDuration()
                  currNote.setDuration(newDuration)

                  phrase.removeNote(index + 1)

               index -= 1

      def tiePart(part):
         """"""
         for phrase in part.getPhraseList():
            tiePhrase(phrase)

      def tieScore(score):
         """"""
         for part in score.getPartList():
            tiePart(part)

      # check type of material and call the appropriate function
      if isinstance(material, Score):
         tieScore(material)

      elif isinstance(material, Part):
         tiePart(material)

      elif isinstance(material, Phrase):
         tiePhrase(material)

      else:   # error check
         raise TypeError( "Unrecognized material type " + str(type(material)) + " - expected Phrase, Part, or Score." )

   @staticmethod
   def transpose(material, steps, scale=CHROMATIC_SCALE, key=0):
      """Shift the pitch of every note, in place.

      With no scale, steps are semitones (for example, 12 raises everything by an octave).
      With a scale and key, steps are scale degrees instead, keeping the music in that key.

      Args:
          material (Note, Phrase, Part, or Score): The music to change.
          steps (int): How far to shift, in semitones, or in scale degrees when a scale is given.
          scale (list[int], optional): The scale to shift within, a list of pitch classes between 0 and 11. If omitted, the shift is chromatic (by semitones).
          key (int, optional): The scale's root pitch class, from 0 to 11, where 0 means C.
      """
      # do some basic error checking
      if not isinstance(material, (Note, Phrase, Part, Score)):
         raise TypeError(f'Mod.transpose(): material must be a Note, Phrase, Part, or Score (it was {type(material)})')
      elif not isinstance(steps, int):
         raise TypeError(f'Mod.transpose(): steps must be an integer (it was {type(steps)})')

      # define support methods
      def transposeNote(note):
         """"""
         pitch  = note.getPitch()

         if note.isRest():  # rests aren't transposable, so we can skip the work
            pass

         elif not isinstance(pitch, int) or (pitch < 0 or pitch > 127):  # if pitch isn't an integer MIDI pitch, transposing won't work
            pass

         else:  # otherwise, we can start transposing
            pitchClass = (pitch - key) % 12
            octave     = (pitch - key) // 12
            degree     = None

            # find the degree in the scale
            if pitchClass in scale:  # use the pitch in the scale
               degree = scale.index(pitchClass)
            else:                    # find the nearest lower pitch in scale
               pitchClassesInScale = [s for s in scale if s <= pitchClass]
               scalePitchClass = None

               if pitchClassesInScale:
                  scalePitchClass = max(pitchClassesInScale)
               else:                 # there isn't a nearest lower pitch, so move down an octave
                  scalePitchClass = max(scale)
                  octave = octave - 1

               degree = scale.index(scalePitchClass)

            # transpose within the scale
            newDegree = degree + steps

            # adjust octave as needed
            octaveShift, newDegree = divmod(newDegree, len(scale))
            newOctave = octave + octaveShift

            # if newDegree is negative, move down an octave
            if newDegree < 0:
               newDegree = newDegree + len(scale)
               newOctave = newOctave - 1

            # find transposed pitch
            newPitch = key + newOctave * 12 + scale[newDegree]

            # clamp to MIDI pitch range
            newPitch = min(127, (max(0, newPitch)))

            note.setPitch(newPitch)
      #### end transposeNote()

      def transposePhrase(phrase):
         for note in phrase.getNoteList():
            transposeNote(note)

      def transposePart(part):
         for phrase in part.getPhraseList():
            transposePhrase(phrase)

      def transposeScore(score):
         for part in score.getPartList():
            transposePart(part)

      # time to actually do the work
      if isinstance(material, Score):
         transposeScore(material)
      elif isinstance(material, Part):
         transposePart(material)
      elif isinstance(material, Phrase):
         transposePhrase(material)
      elif isinstance(material, Note):
         transposeNote(material)
      else:   # error check
         raise TypeError( "Unrecognized material type " + str(type(material)) + " - expected Note, Phrase, Part, or Score." )


#######################################################################################
##### AudioSample #####################################################################
#######################################################################################

_activeAudioSamples = []   # keep track of active AudioSample instances for cleanup

class AudioSample:
   """Play a sound loaded from an audio file, with control over pitch, volume, and panning.

   An AudioSample can be played once, looped, paused, resumed, and stopped. It has a base
   pitch (the recorded sound's own pitch), so it can be pitch-shifted to play other
   pitches or frequencies. It is polyphonic: several voices can play at once and
   independently, so it can sound chords. Supported files are WAV and AIF (16-, 24-, and
   32-bit PCM, and 32-bit float).

   Args:
       filename (str): The audio file to load (a WAV or AIF file).
       actualPitch (int or float, optional): The recorded sound's own pitch, as a MIDI pitch from 0 to 127, or a frequency in hertz (8.17 to 12600.0). Defaults to A4 (440 Hz).
       volume (int, optional): How loud the sample is, from 0 to 127.
       voices (int, optional): How many voices can play at once, for polyphony.
   """

   def __init__(self, filename, actualPitch=A4, volume=127, voices=16):
      from PythonMusic.RealtimeAudioPlayer import _RealtimeAudioPlayer   # lower-level audio playback
      import os        # file path operations

      # Relative paths resolve against the current working directory -- same
      # convention as gui.Icon().  Under PEM, cwd is set to the source
      # script's folder before the run; standalone runs follow the usual
      # Python rule (cwd = wherever the interpreter was launched from).
      if not os.path.isfile(filename):
         raise FileNotFoundError(f"Audio file '{filename}' not found.")

      # file exists, so continue
      self.filename = filename

      # remember how many total voices we have
      self.maxVoices = voices

      # resolve actualPitch to actualPitch (MIDI) and actualFrequency (Hz)
      if isinstance(actualPitch, int) and 0 <= actualPitch <= 127:
         # MIDI pitch provided (0-127) - convert to frequency
         self.actualPitch = float(actualPitch)   # store as float for precision
         self.actualFrequency = noteToFreq(self.actualPitch)   # convert to Hz

      elif isinstance(actualPitch, float):
         # frequency provided in Hz - convert to MIDI pitch
         self.actualFrequency = actualPitch   # store the frequency directly
         self.actualPitch, _ = freqToNote(actualPitch)   # convert to MIDI pitch

         # validate that the resulting MIDI pitch is within valid range
         if not (0 <= self.actualPitch <= 127):
            print(f"Warning: Frequency {actualPitch}Hz results in MIDI pitch {self.actualPitch}, which is outside the 0-127 range. Clamping to nearest valid.")
            self.actualPitch = max(0.0, min(127.0, self.actualPitch))   # clamp to valid range
            self.actualFrequency = noteToFreq(self.actualPitch)   # recalculate frequency from clamped pitch

      else:
         # invalid pitch type - default to A4 and raise error
         self.actualPitch = float(A4)   # default to A4 (440Hz)
         self.actualFrequency = noteToFreq(self.actualPitch)   # calculate default frequency
         raise TypeError(f"actualPitch ({actualPitch}) must be an int (0-127) or float (Hz). Defaulting to A4.")

      # validate and set the initial volume for all voices
      if not (isinstance(volume, int) and 0 <= volume <= 127):
         print(f"Warning: Volume ({volume}) is invalid. Must be an integer between 0 and 127. Defaulting to 127.")
         self.initialVolume = 127   # use maximum volume as fallback

      else:
         self.initialVolume = volume   # use the provided volume

      # initialize internal lists for managing multiple voices
      # each voice has its own state that can be independently controlled
      self._players = []               # RealtimeAudioPlayer instances for each voice
      self._currentPitches = []        # current MIDI pitch for each voice
      self._currentFrequencies = []    # current frequency (Hz) for each voice
      self._currentVolumes = []        # current API volume (0-127) for each voice
      self._currentPannings = []       # current API panning (0-127) for each voice
      self._isPausedFlags = []         # if each voice is currently paused
      self._currentLoopSettings = []   # loop settings for each voice

      # iterate to create each of the parallel sound pipelines
      # NOTE: a RealtimeAudioPlayer instance is needed to handle lower-level playback
      for i in range(self.maxVoices):

         try:   # create a new RealtimeAudioPlayer for this voice
            # the actualPitch should be the base pitch of the sound file
            player = _RealtimeAudioPlayer(filepath=self.filename, actualPitch=int(self.actualPitch), loop=False)
            self._players.append(player)   # keep track of player for each voice

         except Exception as e:
            # if a player fails to initialize, provide detailed error context
            # this helps diagnose issues with audio file loading or player creation
            raise RuntimeError(f"Failed to initialize RealtimeAudioPlayer for voice {i} with file '{self.filename}': {e}")

         # initialize current state values for this voice
         self._currentPitches.append(self.actualPitch)           # start at base pitch
         self._currentFrequencies.append(self.actualFrequency)   # start at base frequency
         self._currentVolumes.append(self.initialVolume)         # start at initial volume
         self._currentPannings.append(64)                        # default API panning: 64 (center)
         self._isPausedFlags.append(False)                       # start as not paused

         # initialize loop settings for this voice
         self._currentLoopSettings.append({
            'active': False,                    # whether looping is currently active
            'loopCountTarget': 0,               # target number of loops (0 = no loop)
            'loopRegionStartFrame': 0.0,        # start frame of loop region
            'loopRegionEndFrame': -1.0,         # end frame of loop region (-1 = to end)
            'loopsPerformedCurrent': 0,         # current loop count
            'playDurationSourceFrames': -1.0    # play duration in frames (-1 = to end)
         })

         # set initial parameters on the RealtimeAudioPlayer instance
         # convert API values to internal factor values used by the player

         # volume conversion: API (0-127) to Factor (0.0-1.0)
         player.setVolumeFactor(self.initialVolume / 127.0)

         # panning conversion: API (0-127, 64=center) to Factor (-1.0 to 1.0)
         apiPanValue = 64   # initial center panning
         panFactor = (apiPanValue - 63.5) / 63.5
         player.setPanFactor(panFactor)

         # The player's pitch/frequency is already set via its actualPitch during init
         # and corresponds to basePitch/baseFrequency. No need to call setPitch/setFrequency here
         # unless we wanted it to start differently from its base.

      # initialize voice management attributes for polyphonic control
      self.freeVoices = list(range(self.maxVoices))   # holds list of free voices (numbered 0 to maxVoices-1)
      self.voicesAllocatedToPitch = {}   # dictionary of voice lists indexed by pitch (several voices per pitch is possible)

      # register this AudioSample for global cleanup when the program exits
      _activeAudioSamples.append(self)   # for cleanup

   def __str__(self):
      return f'AudioSample(filename={self.filename}, actualPitch={self.actualPitch}, volume={self.getVolume()}, voice={self.maxVoices})'

   def __repr__(self):
      return str(self)

   def play(self, start=0, size=-1, voice=0):
      """Play the sample once.

      Args:
          start (int or float, optional): Where to start playing, in milliseconds from the beginning of the sample.
          size (int, optional): How much to play, in milliseconds; -1 plays to the end.
          voice (int, optional): Which voice to play on, from 0 to one less than the number of voices.
      """
      # validate voice and provide fallback if invalid
      if not (isinstance(voice, int) and 0 <= voice < self.maxVoices):
         print(f"AudioSample.play: Warning - Invalid voice index {voice}. Must be 0-{self.maxVoices-1}. Using voice 0.")
         voice = 0

      # validate start time and provide fallback if invalid
      if not (isinstance(start, (int, float)) and start >= 0):
         print(f"AudioSample.play: Warning - Invalid start time {start}ms. Must be a non-negative number. Using 0ms.")
         start = 0

      # get the RealtimeAudioPlayer instance for this voice
      player = self._players[voice]

      # convert start time from milliseconds to seconds for the player
      startSeconds = start / 1000.0
      startAtBeginning = True   # default to starting from beginning

      # handle case where we want to start playback from a specific position
      if start > 0:
         player.setCurrentTime(startSeconds)   # set the player's playback position
         startAtBeginning = False               # indicate we're not starting from the beginning

      # initialize variables for calculating playback parameters
      calculatePlayDurationSourceFrames = -1.0   # default to play until end
      loopRegionStartFrame = 0.0                 # start frame for the loop region (used by player)

      # calculate the starting frame position if we have a valid frame rate
      if player.getFrameRate() > 0:
          loopRegionStartFrame = (start / 1000.0) * player.getFrameRate() if start > 0 else 0.0

      # handle size parameter to determine playback duration
      if size > 0:   # size is in milliseconds
         sizeSeconds = size / 1000.0   # convert to seconds
         frameRate = player.getFrameRate()

         if frameRate > 0:
            # calculate how many source frames to play based on duration
            calculatePlayDurationSourceFrames = sizeSeconds * frameRate

         else:
            print(f"AudioSample.play: Warning - Could not determine valid frame rate for voice {voice}. 'size' parameter will be ignored.")

      elif size == 0:
         # special case: size=0 means play nothing (0 frames)
         calculatePlayDurationSourceFrames = 0.0

      # store the current playback settings for this voice
      # these settings are used for resume functionality and state tracking
      self._currentLoopSettings[voice] = {
         'active': False,              # signifies this is a play-once (not looping)
         'loopCountTarget': 0,         # ensures the player treats this as non-looping
         'loopRegionStartFrame': loopRegionStartFrame,   # starting frame position
         'loopRegionEndFrame': -1.0,   # not critical for non-looping, player uses targetEndSourceFrame
         'loopsPerformedCurrent': 0,   # reset loop counter for new playback
         'playDurationSourceFrames': calculatePlayDurationSourceFrames   # store duration for resume
      }

      # start playback on the underlying RealtimeAudioPlayer
      # configure it for single-play (non-looping) with the calculated parameters
      player.play(startAtBeginning=startAtBeginning,   # whether to start from beginning or current position
                  loop=False,   # explicitly disable looping for single playback
                  playDurationSourceFrames=calculatePlayDurationSourceFrames,   # how many frames to play
                  loopRegionStartFrame=loopRegionStartFrame   # starting frame position
                  # initialLoopsPerformed will be 0 (default) for a new play
                  )

      # reset pause state for this voice since we're starting new playback
      self._isPausedFlags[voice] = False

   def loop(self, times=-1, start=0, size=-1, voice=0):
      """Play the sample over and over.

      Args:
          times (int, optional): How many times to repeat; -1 repeats forever.
          start (int or float, optional): Where to start playing, in milliseconds from the beginning of the sample.
          size (int, optional): How much to play, in milliseconds; -1 plays to the end.
          voice (int, optional): Which voice to play on, from 0 to one less than the number of voices.
      """
      # validate voice parameter and provide fallback if invalid
      if not (isinstance(voice, int) and 0 <= voice < self.maxVoices):
         print(f"AudioSample.loop: Warning - Invalid voice index {voice}. Must be 0-{self.maxVoices-1}. Using voice 0.")
         voice = 0

      # validate start time parameter and provide fallback if invalid
      if not (isinstance(start, (int, float)) and start >= 0):
         print(f"AudioSample.loop: Warning - Invalid start time {start}ms. Must be a non-negative number. Using 0ms.")
         start = 0


      player = self._players[voice]   # get RealtimeAudioPlayer instance for this voice
      frameRate = player.getFrameRate()   # get audio file's sample rate

      # calculate starting frame position for the loop region
      loopRegionStartFrames = 0.0   # default to start of file

      if start > 0:   # if a specific start time is specified

         if frameRate > 0:
            # convert milliseconds to frame position: (start_ms / 1000) * frames_per_second
            loopRegionStartFrames = (start / 1000.0) * frameRate

         else:
            print(f"AudioSample.loop: Warning - Invalid frame rate for voice {voice}. 'start' parameter might not work as expected.")

      # calculate the ending frame position for the loop region
      loopRegionEndFrames = -1.0   # default to end of file
      if size > 0:   # size is in milliseconds

         if frameRate > 0:
            startSeconds = start / 1000.0   # convert start time to seconds
            sizeSeconds = size / 1000.0     # convert size to seconds
            # calculate end frame: (start + size) * frame_rate
            loopRegionEndFrames = (startSeconds + sizeSeconds) * frameRate

            # ensure end frame isn't before start frame due to rounding or tiny size
            if loopRegionEndFrames <= loopRegionStartFrames:
               print(f"AudioSample.loop: Warning - Loop 'size' ({size}ms) results in an end point before or at the start point. Will loop entire file from 'start'.")
               loopRegionEndFrames = -1.0   # fallback to loop until end of file from start

         else:
            print(f"AudioSample.loop: Warning - Invalid frame rate for voice {voice}. 'size' parameter will be ignored, looping full file from 'start'.")

      elif size == 0:
         # special case: size=0 is not valid for looping, so loop the entire file
         print("AudioSample.loop: Info - 'size=0' is not a valid duration for a loop segment. Looping entire file from 'start'.")
         loopRegionEndFrames = -1.0   # loop entire file if size is 0

      # determine if the player should start from the beginning of the loop segment
      # NOTE: this is generally true for new loop commands, unless resuming a specific sequence
      startAtBeginningOfLoopSegment = True
      if start > 0:   # if start is specified, we always want to set the current time
         player.setCurrentTime(start / 1000.0)   # convert to seconds for the player

      # map the AudioSample API 'times' parameter to RealtimeAudioPlayer loop settings
      # the 'times' parameter controls how many times the loop region should repeat
      actualLoopCountTarget = times   # pass through the requested loop count
      playerShouldLoop = True         # default to looping enabled

      if times == 0:
         # special case: times=0 means play the segment once without looping
         playerShouldLoop = False     # disable looping in the player
         actualLoopCountTarget = 0    # set target to 0 (play once through the segment)
         # print("AudioSample.loop: Info - 'times=0' means play segment once without looping.")

      # print(f"AudioSample.loop: Calling player.play with: loop={player_should_loop}, targetCount={actual_loop_count_target}, regionStartF={loop_region_start_frames}, regionEndF={loop_region_end_frames}")

      # store current loop settings for this voice
      # used for resume functionality and state tracking
      self._currentLoopSettings[voice] = {
         'active': playerShouldLoop,                    # whether looping is currently active
         'loopCountTarget': actualLoopCountTarget,      # target number of loops to perform
         'loopRegionStartFrame': loopRegionStartFrames, # starting frame of the loop region
         'loopRegionEndFrame': loopRegionEndFrames,     # ending frame of the loop region
         'loopsPerformedCurrent': 0,                    # reset loop counter for new loop command
         'playDurationSourceFrames': -1.0               # not used for active looping (player handles duration)
      }

      # start looping playback on the underlying RealtimeAudioPlayer
      # configure it for looping with the calculated region boundaries and loop count
      player.play(startAtBeginning=startAtBeginningOfLoopSegment,   # whether to start from beginning of loop segment
                  loop=playerShouldLoop,                            # enable/disable looping in the player
                  playDurationSourceFrames=-1.0,                    # not used for looping (player uses loop region)
                  loopRegionStartFrame=loopRegionStartFrames,       # starting frame of the loop region
                  loopRegionEndFrame=loopRegionEndFrames,           # ending frame of the loop region
                  loopCountTarget=actualLoopCountTarget)            # how many times to repeat the loop

      # reset pause state for this voice since we're starting new looped playback
      self._isPausedFlags[voice] = False

   def stop(self, voice=0):
      """Stop the sample playing.

      Args:
          voice (int, optional): Which voice to stop, from 0 to one less than the number of voices.
      """
      # validate voice and provide fallback if invalid
      if not (isinstance(voice, int) and 0 <= voice < self.maxVoices):
         print(f"AudioSample.stop: Warning - Invalid voice index {voice}. Must be 0-{self.maxVoices-1}. Using voice 0.")
         voice = 0

      player = self._players[voice]   # get RealtimeAudioPlayer instance for this voice
      player.stop()     # stop sample playback

      # reset loop settings for this voice to default non-looping
      # used for resume functionality and state tracking
      self._currentLoopSettings[voice] = {
         'active': False,                   # whether looping is currently active
         'loopCountTarget': 0,              # target number of loops to perform
         'loopRegionStartFrame': 0.0,       # starting frame of the loop region
         'loopRegionEndFrame': -1.0,        # ending frame of the loop region
         'loopsPerformedCurrent': 0,        # reset loop counter for new loop command
         'playDurationSourceFrames': -1.0   # not used for active looping (player handles duration)
      }

      self._isPausedFlags[voice] = False # reset pause state on stop

   def isPlaying(self, voice=0):
      """Report whether the sample is currently playing.

      Args:
          voice (int, optional): Which voice to check, from 0 to one less than the number of voices.

      Returns:
          playing (bool): True if the sample is still playing, False otherwise; None if an error occurs.
      """
      # validate voice and return False if invalid
      if not (isinstance(voice, int) and 0 <= voice < self.maxVoices):
         print(f"AudioSample.isPlaying: Warning - Invalid voice index {voice}. Must be 0-{self.maxVoices-1}. Returning False.")
         return None

      else:
         player = self._players[voice]   # get RealtimeAudioPlayer instance for this voice

         # NOTE: player.isPlaying directly reflects if the RealtimeAudioPlayer is active.
         # This will be False if stopped, paused (as pause calls player.stop(immediate=False)),
         # or if playback naturally ended.
         playing = player.isPlaying
         return playing

   def isPaused(self, voice=0):
      """Report whether the sample is currently paused.

      Args:
          voice (int, optional): Which voice to check, from 0 to one less than the number of voices.

      Returns:
          paused (bool): True if the sample is paused, False otherwise; None if an error occurs.
      """
      # validate voice and return None if invalid
      if not (isinstance(voice, int) and 0 <= voice < self.maxVoices):
         print(f"AudioSample.isPaused: Warning - Invalid voice index {voice}. Must be 0-{self.maxVoices-1}. Returning False.")
         return None

      else:
         # return True if voice is paused, False if playing
         paused = self._isPausedFlags[voice]
         return paused

   def pause(self, voice=0):
      """Pause the sample, remembering where it is.

      Use resume() to continue from this point.

      Args:
          voice (int, optional): Which voice to pause, from 0 to one less than the number of voices.
      """
      # validate voice and provide fallback if invalid
      if not (isinstance(voice, int) and 0 <= voice < self.maxVoices):
         print(f"AudioSample.pause: Warning - Invalid voice index {voice}. Must be 0-{self.maxVoices-1}. Using voice 0.")
         voice = 0

      player = self._players[voice]   # get RealtimeAudioPlayer instance for this voice

      if player.isPlaying:   # only pause if it's actually playing
         # store current loops performed from the player *before* stopping it
         currentLoopsPerformedByPlayer = player.getLoopsPerformed()
         self._currentLoopSettings[voice]['loopsPerformedCurrent'] = currentLoopsPerformedByPlayer

         player.stop(immediate=False)        # stop without fade-out
         self._isPausedFlags[voice] = True   # remember this voice is paused

      else:

         # if already stopped or paused, no action needed or print info
         if self._isPausedFlags[voice]:
            print(f"AudioSample.pause: Voice {voice} is already paused.")

         else:
            print(f"AudioSample.pause: Voice {voice} is not currently playing, cannot pause.")

   def resume(self, voice=0):
      """Resume the sample from where it was paused.

      Args:
          voice (int, optional): Which voice to resume, from 0 to one less than the number of voices.
      """
      # validate voice and provide fallback if invalid
      if not (isinstance(voice, int) and 0 <= voice < self.maxVoices):
         print(f"AudioSample.resume: Warning - Invalid voice index {voice}. Must be 0-{self.maxVoices-1}. Using voice 0.")
         voice = 0

      player = self._players[voice]   # get RealtimeAudioPlayer instance for this voice
      loopSettings = self._currentLoopSettings[voice]   # loop settings for voice

      if self._isPausedFlags[voice]:

         # this voice was explicitly paused by AudioSample.pause()
         if player.isPlaying:
            # This case should ideally not be hit if pause correctly stops the player.
            # if it is hit, it means player is playing despite being paused from AudioSample's view.
            print(f"AudioSample.resume: Voice {voice} was paused but player is already playing. Resuming anyway and clearing pause flag.")

         # else:
            # Expected path: paused and player is not playing, so resume.
            # print(f"AudioSample.resume: Resuming explicitly paused voice {voice}.")

         if not loopSettings['active']:   # if it was a single play being resumed
            playDurationForResume = loopSettings.get('playDurationSourceFrames', -1.0)
         else:   # it was a loop being resumed
            playDurationForResume = -1.0   # not used for looping (player uses loop region)

         # start the player
         player.play(
            startAtBeginning=False,                                       # whether to start from beginning of loop segment
            loop=loopSettings['active'],                                  # enable/disable looping in the player
            playDurationSourceFrames=playDurationForResume,               # not used for looping (player uses loop region)
            loopRegionStartFrame=loopSettings['loopRegionStartFrame'],    # starting frame of the loop region
            loopRegionEndFrame=loopSettings['loopRegionEndFrame'],        # ending frame of the loop region
            loopCountTarget=loopSettings['loopCountTarget'],              # how many times to repeat the loop
            initialLoopsPerformed=loopSettings['loopsPerformedCurrent']   # how many loops performed already
         )
         self._isPausedFlags[voice] = False   # remember this voice is resumed

      else:

         # this voice was NOT explicitly paused by AudioSample.pause()
         if player.isPlaying:
            print(f"AudioSample.resume: Voice {voice} is already playing and was not paused!")

         else:
            print(f"AudioSample.resume: Voice {voice} was not paused via AudioSample.pause(). Call pause() first to use resume, or play() to start.")
            # do not change _isPausedFlags[voice] here, it's already False.
            # do not start playback.

   def setFrequency(self, freq, voice=0):
      """Set the sample's playback frequency, pitch-shifting it.

      Like setPitch(), but finer. This lets the sound land between the standard pitches. For
      example, frequency 440 Hz is the same as pitch A4.

      Args:
          freq (int or float): The new playback frequency, in hertz (8.17 to 12600.0).
          voice (int, optional): Which voice to set, from 0 to one less than the number of voices.
      """
      if not (isinstance(voice, int) and 0 <= voice < self.maxVoices):
         print(f"AudioSample.setFrequency: Warning - Invalid voice index {voice}. Must be 0-{self.maxVoices-1}. Using voice 0.")
         voice = 0

      elif not (isinstance(freq, (int, float)) and freq > 0):
         print(f"AudioSample.setFrequency: Warning - Invalid frequency value {freq}Hz. Must be a positive number. No change.")

      else:
         freqFloat = float(freq)

         # only update frequency if the value has changed, to avoid unnecessary audio engine updates
         if freqFloat != self._currentFrequencies[voice]:
            player = self._players[voice]   # get RealtimeAudioPlayer instance for this voice
            player.setFrequency(freqFloat)   # set frequency immediately

            self._currentFrequencies[voice] = freqFloat   # remember frequency of this voice
            self._currentPitches[voice] = player.getPitch()   # pitch also changes in player

   def getFrequency(self, voice=0):
      """Return the sample's current playback frequency.

      Args:
          voice (int, optional): Which voice to read, from 0 to one less than the number of voices.

      Returns:
          frequency (float): The current playback frequency, in hertz (8.17 to 12600.0); None if an error occurs.
      """
      if not (isinstance(voice, int) and 0 <= voice < self.maxVoices):
         print(f"AudioSample.getFrequency(): Voice ({voice}) should range from 0 to {self.maxVoices}.")
         return None

      else:
         frequency = self._currentFrequencies[voice]
         return frequency

   def setPitch(self, pitch, voice=0):
      """Set the sample's playback pitch, pitch-shifting it from its base pitch.

      Args:
          pitch (int or float): The new playback pitch, as a MIDI pitch from 0 to 127.
          voice (int, optional): Which voice to set, from 0 to one less than the number of voices.
      """
      if not (isinstance(voice, int) and 0 <= voice < self.maxVoices):
         print(f"AudioSample.setPitch(): Voice ({voice}) should range from 0 to {self.maxVoices}.")

      elif not (isinstance(pitch, (int, float)) and 0 <= pitch <= 127):
         print(f"AudioSample.setPitch(): Pitch ({pitch}) must be a number between 0 and 127.")

      else:
         pitchFloat = float(pitch)

         # only update pitch if the value has changed, to avoid unnecessary frequency conversions and audio engine updates
         if pitchFloat != self._currentPitches[voice]:
            # convert pitch to frequency and call setFrequency
            frequency = noteToFreq(pitchFloat)
            self.setFrequency(frequency, voice)

            # update pitch tracking (frequency tracking is handled by setFrequency)
            self._currentPitches[voice] = pitchFloat

   def getPitch(self, voice=0):
      """Return the sample's current playback pitch.

      This may differ from the sample's base pitch if it has been pitch-shifted.

      Args:
          voice (int, optional): Which voice to read, from 0 to one less than the number of voices.

      Returns:
          pitch (int): The current playback pitch, as a MIDI pitch from 0 to 127; None if an error occurs.
      """
      if not (isinstance(voice, int) and 0 <= voice < self.maxVoices):
         print(f"AudioSample.getPitch(): Voice ({voice}) should range from 0 to {self.maxVoices}.")
         return None

      else:
         pitch = self._currentPitches[voice]
         return pitch

   def setPanning(self, panning, voice=0):
      """Set the sample's stereo position.

      Args:
          panning (int): Stereo position from 0 (left) to 127 (right).
          voice (int, optional): Which voice to set, from 0 to one less than the number of voices.
      """
      if not (isinstance(voice, int) and 0 <= voice < self.maxVoices):
         print(f"AudioSample.setPanning(): Voice ({voice}) should range from 0 to {self.maxVoices}.")

      elif not (isinstance(panning, int) and 0 <= panning <= 127):
         print(f"AudioSample.setPanning: Warning - Invalid panning value {panning}. Must be an integer between 0 and 127. No change.")

      else:
         # only update panning if the value has changed, to avoid unnecessary audio engine updates
         if panning != self._currentPannings[voice]:
            player = self._players[voice]   # get RealtimeAudioPlayer instance for this voice

            # convert API pan (0-127, 64=center) to player factor (-1.0 to 1.0)
            # (api_pan - 63.5) / 63.5 ensures that 64 -> ~0.0, 0 -> -1.0, 127 -> 1.0
            panFactor = (panning - 63.5) / 63.5
            player.setPanFactor(panFactor)

            self._currentPannings[voice] = panning   # remember panning for this voice

   def getPanning(self, voice=0):
      """Return the sample's stereo position.

      Args:
          voice (int, optional): Which voice to read, from 0 to one less than the number of voices.

      Returns:
          panning (int): Stereo position from 0 (left) to 127 (right); None if an error occurs.
      """
      if not (isinstance(voice, int) and 0 <= voice < self.maxVoices):
         print(f"AudioSample.getPanning(): Voice ({voice}) should range from 0 to {self.maxVoices}.")
         return None

      else:
         panning = self._currentPannings[voice]
         return panning

   def setVolume(self, volume, delay=2, voice=0):
      """Set how loud the sample is.

      Args:
          volume (int): How loud to make the sample, from 0 to 127.
          delay (int or float, optional): How long to take making the change, in milliseconds.
          voice (int, optional): Which voice to set, from 0 to one less than the number of voices.
      """
      if not (isinstance(volume, int) and 0 <= volume <= 127):
         print(f"AudioSample.setVolume: Warning - Invalid volume {volume} for voice {voice}. Must be an integer between 0 and 127. No change.")

      elif not (isinstance(delay, (int, float)) and delay >= 0):
         print(f"AudioSample.setVolume: Warning - Invalid delay {delay}. Should be 0 or larger (in milliseconds).")

      elif not (isinstance(voice, int) and 0 <= voice < self.maxVoices):
         print(f"AudioSample.setVolume(): Voice ({voice}) should range from 0 to {self.maxVoices}.")

      else:
         # only update volume if the value has changed, to avoid unnecessary ramp creation and audio engine updates
         if volume != self._currentVolumes[voice]:
            player = self._players[voice]   # get RealtimeAudioPlayer instance for this voice
            targetVolumeFactor = volume / 127.0

            # enforce minimum delay to prevent audio clicks/discontinuities
            minDelay = 2.0   # minimum 2ms ramp to prevent audible artifacts
            effectiveDelay = max(delay, minDelay)

            # calculate appropriate step size (should be smaller than total duration)
            # use smaller steps for short ramps, larger steps for long ramps
            stepMs = min(effectiveDelay / 2.0, 10)   # at least 2 steps, max 10ms intervals

            # define a callback for the ramp to update the player's volume factor
            def rampCallback(currentVolumeFactor):
               player.setVolumeFactor(currentVolumeFactor)

            # always use ramp for smooth transitions (enforcing minimum delay)
            currentApiVolume = self._currentVolumes[voice]
            currentVolumeFactor = currentApiVolume / 127.0

            volumeRamp = LinearRamp(
               delayMs=float(effectiveDelay),
               startValue=currentVolumeFactor,
               endValue=targetVolumeFactor,
               action=rampCallback,
               stepMs=stepMs
            )
            volumeRamp.start()   # start volume ramp

            self._currentVolumes[voice] = volume   # store target API volume for this voice

   def getVolume(self, voice=0):
      """Return how loud the sample is.

      Args:
          voice (int, optional): Which voice to read, from 0 to one less than the number of voices.

      Returns:
          volume (int): How loud the sample is, from 0 to 127; None if an error occurs.
      """
      if not (isinstance(voice, int) and 0 <= voice < self.maxVoices):
         print(f"AudioSample.getVolume(): Voice ({voice}) should range from 0 to {self.maxVoices}.")
         return None

      else:
         volume = self._currentVolumes[voice]
         return volume

   def _allocateVoiceForPitch(self, pitch):
      """"""
      if isinstance(pitch, int) and (0 <= pitch <= 127):   # a MIDI pitch?
         # yes, so convert pitch from MIDI number (int) to Hertz (float)
         pitch = noteToFreq(pitch)

      elif not isinstance(pitch, float):   # is pitch a frequency (a float, in Hz)?
         raise TypeError("Pitch (" + str(pitch) + ") should be an int (range 0 and 127) or float (such as 440.0).")

      # now, assume pitch contains a frequency (float)

      # get next free voice (if any)
      voiceForThisPitch = self._getNextFreeVoice()

      if voiceForThisPitch is not None:   # if a free voice exists...

         # associate it with this pitch
         if pitch not in self.voicesAllocatedToPitch:   # new pitch (not sounding already)?
            self.voicesAllocatedToPitch[pitch] = [voiceForThisPitch]         # remember that this voice is playing this pitch

         else:   # there is at least one other voice playing this pitch, so...
            self.voicesAllocatedToPitch[pitch].append( voiceForThisPitch )   # append this voice (mimicking MIDI standard for polyphony of same pitches!!!)

         # now, self.pitchSounding remembers that this voice is associated with this pitch

      # now, return new voice for this pitch (it could be None, if no free voices exist!)
      return voiceForThisPitch

   def _getNextFreeVoice(self):
      """"""
      if len(self.freeVoices) > 0:   # are there some free voices?
         freeVoice = self.freeVoices.pop(0)   # get the first available one

      else:   # all voices are being used
         freeVoice = None

      return freeVoice

   def _getVoiceForPitch(self, pitch):
      """"""
      if isinstance(pitch, int) and (0 <= pitch <= 127):   # a MIDI pitch?
         # yes, so convert pitch from MIDI number (int) to Hertz (float)
         pitch = noteToFreq(pitch)

      elif not isinstance(pitch, float):   # if pitch a frequency (a float, in Hz)
         raise TypeError("Pitch (" + str(pitch) + ") should be an int (range 0 and 127) or float (such as 440.0).")

      # now, assume pitch contains a frequency (float)

      voice = None   # initialize

      if pitch in self.voicesAllocatedToPitch and len( self.voicesAllocatedToPitch[pitch] ) > 0:   # does this pitch have voices allocated to it?
         voice = self.voicesAllocatedToPitch[pitch][0]   # first voice used for this pitch

      else:   # pitch is not currently sounding, so...
         voice = None
         # raise ValueError("Pitch (" + str(pitch) + ") is not currently playing!!!")

      # now, let them know which voice was freed (if any)
      return voice

   def _deallocateVoiceForPitch(self, pitch):
      """"""
      if isinstance(pitch, int) and (0 <= pitch <= 127):   # a MIDI pitch?
         # yes, so convert pitch from MIDI number (int) to Hertz (float)
         pitch = noteToFreq(pitch)

      elif not isinstance(pitch, float):   # if pitch a frequency (a float, in Hz)
         raise TypeError("Pitch (" + str(pitch) + ") should be an int (range 0 and 127) or float (such as 440.0).")

      # now, assume pitch contains a frequency (float)
      if pitch in self.voicesAllocatedToPitch and len( self.voicesAllocatedToPitch[pitch] ) > 0:   # does this pitch have voices allocated to it?
         freedVoice = self.voicesAllocatedToPitch[pitch].pop(0)   # deallocate first voice used for this pitch
         self.freeVoices.append( freedVoice )                     # and return it back to the pool of free voices

      else:   # pitch is not currently sounding, so...
         raise ValueError("Pitch (" + str(pitch) + ") is not currently playing!!!")

      # done!!!

   def getFrameRate(self):
      """Return the sample's recording rate.

      The rate is fixed by the audio file and is the same for every voice. To change how the
      sample sounds, use setFrequency() or setPitch() instead.

      Returns:
          frameRate (float): The recording rate, in hertz, for example 44100.0; None if an error occurs.
      """
      if not self._players:
         print("AudioSample.getFrameRate: Warning - No audio players initialized for this sample.")
         return None

      else:
         # all players share the same frame rate as they are from the same file
         frameRate = self._players[0].getFrameRate()
         return frameRate

   def __del__(self):
      """"""
      # check if already closed or not initialized
      if not hasattr(self, '_players') or not self._players:
         return

      for player in self._players:

         if player:   # does player exist?
            try:
               player.close()   # close player

            except Exception as e:
               # print(f"AudioSample.close: Error closing player for '{self.filename}': {e}")
               pass

      self._players = []   # clear list to help with garbage collection and prevent reuse

      # remove from global list if present
      if self in _activeAudioSamples:
         try:
            _activeAudioSamples.remove(self)   # remove active sample

         except ValueError:
            # this can happen if close() is called multiple times
            pass


def _cleanupAudioSamples():
   """"""
   global _activeAudioSamples

   # Phase 1: initiate fade-out on all playing voices
   playing_players = []
   for sample in _activeAudioSamples:
      if hasattr(sample, '_players'):
         for player in sample._players:
            if player and player.isPlaying:
               player.stop()   # 20ms fade out
               playing_players.append(player)

   # Phase 2: wait for fade-outs to complete
   # if playing_players:
      # fade out is 20ms, so 25ms should be enough
      time.sleep(0.025)

   # Phase 3: close all players
   for sample in list(_activeAudioSamples):
      if hasattr(sample, '_players'):
         for player in sample._players:
             if player:
               try:
                  player.close()
               except Exception:
                  pass # ignore errors during final cleanup

# register cleanup function to be called at Python interpreter exit
atexit.register(_cleanupAudioSamples)

# Note on cleanup: sounddevice itself has an atexit handler that terminates PortAudio.
# Our cleanupAudioSamples function is a best-effort attempt to explicitly close all
# AudioSample instances and their underlying RealtimeAudioPlayer streams before that.
# The RealtimeAudioPlayer.close() method is designed to be robust and will not error
# if PortAudio has already been terminated by sounddevice's cleanup, preventing crashes
# if our atexit handler runs after sounddevice's.


#######################################################################################
##### Envelope ########################################################################
#######################################################################################

class Envelope():
   """Shape an audio sample's volume over time, giving its sound an attack, sustain, and fade.

   An envelope has four parts:
   - attack: volumes to rise or fall through at given times, starting from the start of the sound;
   - delay: how long to then take reaching the sustain volume;
   - sustain: the volume held through the body of the sound, however long it lasts;
   - release: how long the sound takes to fade to silence after it ends.

   All times are in milliseconds, each measured from the previous one. The exceptions are the first
   attack time (measured from the start of the sound) and the release time (which extends
   past the end of the sound). Volumes run from 0.0 (silence) to 1.0 (full).

   Args:
       attackTimes (list[int], optional): The attack times, in milliseconds, each measured from the previous one (the first from the start of the sound).
       attackVolumes (list[float], optional): The volumes to reach at the attack times, each from 0.0 to 1.0; parallel to attackTimes.
       delayTime (int, optional): How long to take reaching the sustain volume, in milliseconds after the last attack time.
       sustainVolume (float, optional): The volume held through the body of the sound, from 0.0 to 1.0.
       releaseTime (int, optional): How long the sound takes to fade to silence after it ends, in milliseconds.
   """

   def __init__(self, attackTimes=[2, 20], attackVolumes=[0.5, 0.8], delayTime=20, sustainVolume=1.0, releaseTime=150):
      self.attackTimes    = []     # in milliseconds, relative from previous time
      self.attackVolumes  = []     # and the corresponding volumes
      self.delayTime      = 0      # in milliseconds, relative from previous time
      self.sustainVolume  = 0.0    # to reach this volume
      self.releaseTime    = 0      # in milliseconds, length of fade out - beyond END of sound

      # udpate above values (this will do appropriate error checks, so that we do not repeat that code twice here)
      self.setAttackTimesAndVolumes(attackTimes, attackVolumes)
      self.setDelayTime(delayTime)
      self.setSustainVolume(sustainVolume)
      self.setReleaseTime(releaseTime)

   def __str__(self):
      return f'Envelope(attackTimes = {self.attackTimes}, attackVolumes = {self.attackVolumes}, delayTime = {self.delayTime}, sustainVolume = {self.sustainVolume}, releaseTime = {self.releaseTime})'

   def __repr__(self):
      return str(self)

   def setAttackTimesAndVolumes(self, attackTimes, attackVolumes):
      """Set the envelope's attack times and the volumes reached at them.

      The two lists are parallel and must be the same length.

      Args:
          attackTimes (list[int]): The attack times, in milliseconds, each measured from the previous one (the first from the start of the sound).
          attackVolumes (list[float]): The volumes to reach at those times, each from 0.0 to 1.0.
      """
      # make sure attack times and volumes are parallel
      if len(attackTimes) != len(attackVolumes):

         raise IndexError("Attack times and volumes must have the same length.")

      # make sure attack times are all ints, greater than zero
      for attackTime in attackTimes:

         if attackTime < 0:

            raise ValueError("Attack times should be zero or positive (found " + str(attackTime) + ").")

      # make sure attack volumes are all floats between 0.0 and 1.0 (inclusive).
      for attackVolume in attackVolumes:

         if attackVolume < 0.0 or 1.0 < attackVolume:

            raise ValueError("Attack volumes should be between 0.0 and 1.0 (found " + str(attackVolume) + ").")

      # all well, so update
      self.attackTimes   = attackTimes
      self.attackVolumes = attackVolumes

   def getAttackTimesAndVolumes(self):
      """Return the envelope's attack times and the volumes reached at them.

      Returns:
          attackTimes (list[int]): The attack times, in milliseconds.
          attackVolumes (list[float]): The volumes reached at those times, each from 0.0 to 1.0.
      """
      attackTimes   = self.attackTimes
      attackVolumes = self.attackVolumes
      return attackTimes, attackVolumes

   def setDelayTime(self, delayTime):
      """Set the envelope's delay time.

      Args:
          delayTime (int): How long to take reaching the sustain volume, in milliseconds after the last attack time.
      """
      # make input value is appropriate
      if delayTime < 0:

         raise ValueError("Delay time must 0 or greater (in milliseconds).")

      # all well, so update
      self.delayTime = delayTime

   def getDelayTime(self):
      """Return the envelope's delay time.

      Returns:
          delayTime (int): The delay time, in milliseconds.
      """
      delayTime = self.delayTime
      return delayTime

   def setSustainVolume(self, sustainVolume):
      """Set the envelope's sustain volume.

      Args:
          sustainVolume (float): The volume held through the body of the sound, from 0.0 to 1.0.
      """
      # make input value is appropriate
      if sustainVolume < 0.0 or sustainVolume > 1.0:

         raise ValueError("Sustain volume must be between 0.0 and 1.0.")

      # all well, so update
      self.sustainVolume = sustainVolume

   def getSustainVolume(self):
      """Return the envelope's sustain volume.

      Returns:
          sustainVolume (float): The sustain volume, from 0.0 to 1.0.
      """
      sustainVolume = self.sustainVolume
      return sustainVolume

   def setReleaseTime(self, releaseTime):
      """Set the envelope's release time.

      Args:
          releaseTime (int): How long the sound takes to fade to silence after it ends, in milliseconds.
      """
      # make input value is appropriate
      if releaseTime < 0:

         raise ValueError("Release time must 0 or greater (in milliseconds).")

      # all well, so update
      self.releaseTime = releaseTime

   def getReleaseTime(self):
      """Return the envelope's release time.

      Returns:
          releaseTime (int): The release time, in milliseconds.
      """
      releaseTime = self.releaseTime
      return releaseTime

   def performAttackDelaySustain(self, audioSample, volume, voice):
      """Apply the envelope's attack, delay, and sustain to a voice of an audio sample.

      This starts the volume changes that shape the beginning of the sound. Usually called
      for you by Play.audioOn().

      Args:
          audioSample (AudioSample): The audio sample to shape.
          volume (int): The note's overall volume, from 0 to 127, that the envelope's levels are taken relative to.
          voice (int): Which voice of the audio sample to shape.
      """
      # NOTE: In order to allow the same envelope to be re-used by different audio samples, we place inside the audio sample
      #       a dictionary of timers, indexed by voice.  This way different audio samples will not compete with each other, if they are all
      #       using the same envelope.
      #
      # Each voice has its own list of timers - implementing the envelope, while it is sounding
      # This way, we can stop these timers, if the voice sounds less time than what the envelope - not an error (we will try and do our best)

      # initialize envelope timers for this audio sample
      if "envelopeTimers" not in dir(audioSample):   # is this the first time we see this audio sample?

         audioSample.envelopeTimers = {}                # yes, so initiliaze dictionary of envelope timers

      # now, we have a dictionary of envelope timers

      # next, initiliaze list of timers for this voice (we may assume that none exists...)
      audioSample.envelopeTimers[voice] = []

      # set initial volume to zero
      audioSample.setVolume(volume = 0, delay = 2, voice = voice)

      # initialize variables
      maxVolume = volume   # audio sample's requested volume... everything will be adjusted relative to that
      nextTime  = 0        # next time to begin volume adjustment - start at beginning of sound

      # schedule attack timers
      for attackTime, attackVolume in zip(self.attackTimes, self.attackVolumes):

         # adjust volume appropriately
         volume = int(maxVolume * attackVolume)   # attackVolume ranges between 0.0 and 1.0, so we treat it as relative factor

         # schedule volume change over this attack time
         # NOTE: attackTime indicates how long this volume change should take!!!
         timer = Timer(nextTime, audioSample.setVolume, [volume, attackTime, voice], False)
         #print "attack set - volume, delay, voice =", volume, nextTime, voice #***

         # remember timer
         audioSample.envelopeTimers[voice].append( timer )

         # advance time
         nextTime = nextTime + attackTime

      # now, all attack timers have been created

      # next, create timer to handle delay and sustain setting
      volume   = int(maxVolume * self.sustainVolume)   # sustainVolume ranges between 0.0 and 1.0, so we treat it as relative factor

      # schedule volume change over delay time
      # NOTE: delay time indicates how long this volume change should take!!!
      timer = Timer(nextTime, audioSample.setVolume, [volume, self.delayTime, voice], False)
      #print "delay set - volume, voice =", volume, voice #***

      # remember timer
      audioSample.envelopeTimers[voice].append( timer )

      # beginning of envelope has been set up, so start timers to make things happen
      for timer in audioSample.envelopeTimers[voice]:
         timer.start()

      # done!!!

   def performReleaseAndStop(self, audioSample, voice):
      """Apply the envelope's release (fade-out) to a voice of an audio sample, then stop it.

      Usually called for you by Play.audioOff().

      Args:
          audioSample (AudioSample): The audio sample to fade out and stop.
          voice (int): Which voice of the audio sample to fade out and stop.
      """
      # stop any remaining timers, and empty list
      for timer in audioSample.envelopeTimers[voice]:
         timer.stop()

      # empty list of timers - they are not needed anymore (clean up for next use...)
      del audioSample.envelopeTimers[voice]

      # turn volume down to zero, slowly, over release time milliseconds
      audioSample.setVolume(volume = 0, delay = self.releaseTime, voice = voice)
      #print "release set - volume, voice =", 0, voice #***

      # and schedule sound to stop, after volume has been turned down completely
      someMoreTime = 5   # to give a little extra time for things to happen (just in case) - in milliseconds (avoids clicking...)
      timer = Timer(self.releaseTime + someMoreTime, audioSample.stop, [voice], False)
      timer.start()

      # done!!!


#######################################################################################
##### MidiSequence ####################################################################
#######################################################################################

class MidiSequence():
   """Play MIDI music, with live control over pitch, tempo, and volume.

   Build a MidiSequence from music library material (Note, Phrase, Part, or Score) or
   from a MIDI file. It can be played once, looped, paused, resumed, and stopped, and its
   pitch, tempo, and volume can be changed while it plays.

   Args:
       material (str, Note, Phrase, Part, or Score): The music to play, or the filename of a MIDI file (.mid).
       pitch (int or float, optional): The pitch to play at, as a MIDI pitch. Defaults to A4.
       volume (int, optional): How loud to play, from 0 to 127.
   """

   def __init__(self, material, pitch=A4, volume=127):

      # determine what type of material we have
      if isinstance(material, str):   # a string?
         self.filename = material                # assume it's an external MIDI filename

         # load and create the MIDI sample
         tempScore = Score()                    # create an empty score
         Read.midi(tempScore, self.filename)    # load the external MIDI file
         self.score = tempScore

      else:   # determine what type of material we have

         # and do necessary datatype wrapping (MidiSynth() expects a Score)
         if isinstance(material, Note):
            material = Phrase(material)
         if isinstance(material, Phrase):   # no elif - we need to successively wrap from Note to Score
            material = Part(material)
            material.setInstrument(-1)     # indicate no default instrument (needed to access global instrument)
         if isinstance(material, Part):     # no elif - we need to successively wrap from Note to Score
            material = Score(material)
         if isinstance(material, Score):
            self.score = material     # and remember it
         else:   # error check
            raise TypeError(f"MidiSequence(): Unrecognized type {type(material)}, expected Note, Phrase, Part, or Score.")

      # now, self.score contains a Score object

      # build a playable event list from transcription material (Note/Phrase/Part/Score)
      # extract flattened note events with absolute ms timing using current tempos
      self._events = self._extractEvents(self.score)   # list of dicts (startMs, endMs, pitch, velocity, channel, instrument, panning)

      # playback state
      self._totalDurationMs = 0 if not self._events else self._events[-1]['endMs']   # total duration of the sequence
      self._positionMs = 0.0                      # current playback position within sequence
      self._playing = False                       # whether advancing timeline
      self._loop = False                          # loop playback flag (set via loop())
      self._transposeSemitones = 0                # global transpose for future notes
      self.defaultPitch = pitch                   # stored for compatibility (not directly used)
      self.defaultTempo = self.score.getTempo()   # base tempo captured at extraction
      self.tempoFactor = 1.0                      # multiplier for playback speed (setTempo adjusts this)

      # set volume
      try:
         self.volume = int(volume)   # convert to integer

      except Exception:
         self.volume = 127           # use default volume if conversion fails

      self.volume = max(0, min(127, self.volume))   # clamp volume to valid MIDI range

      # scheduler
      self._tickIntervalMs = 20                # scheduler resolution (ms)
      self._scheduler = Timer(self._tickIntervalMs, self._tick, [], True)   # create repeating timer for playback

      # event progress tracking
      self._nextEventIndex = 0                 # next event to consider starting
      self._activeNotes = []                   # list of dicts for started notes (with endMs) - for timing only

      self._numEvents = len(self._events)   # cache event count to avoid repeated len() calls

   def play(self):
      """Play the sequence once.
      """
      # reset to beginning and start from first event
      self._positionMs = 0.0
      self._nextEventIndex = 0
      self._playing = True         # start advancing timeline

      if not self._scheduler.isRunning():   # is the scheduler already running?
         self._scheduler.start()            # no, so start it

   def loop(self):
      """Play the sequence over and over, forever.
      """
      if self._playing:   # is another play active?
         self.stop()      # yes, so stop it

      self._loop = True        # turn on looping
      self.play()              # and start playing

   def isPlaying(self):
      """Report whether the sequence is currently playing.

      Returns:
          playing (bool): True if the sequence is still playing, False otherwise.
      """
      playing = self._playing
      return playing

   def stop(self):
      """Stop the sequence playing.
      """
      self._playing = False         # stop advancing timeline
      self._positionMs = 0.0        # reset position to beginning
      self._nextEventIndex = 0      # reset event index
      self._loop = False            # turn off looping

   def pause(self):
      """Pause the sequence, remembering where it is.

      Use resume() to continue from this point.
      """
      if self._playing:   # is the sequence already paused?
         self._playing = False   # stop advancing timeline

         # let currently sounding notes finish naturally (Play.note() handles timing)
         # advance next event index to first event strictly after current position
         pos = int(self._positionMs)
         idx = self._nextEventIndex

         while idx < len(self._events) and self._events[idx]['startMs'] <= pos:
            idx += 1

         self._nextEventIndex = idx

   def resume(self):
      """Resume the sequence from where it was paused.
      """
      alreadyPlaying = self._playing   # check if already playing

      # do not retrigger mid-note, continue timeline from current position
      self._playing = True   # start advancing timeline again

      if not alreadyPlaying and not self._scheduler.isRunning():   # is the scheduler not running?
            self._scheduler.start()                                    # no, so start it

   def setPitch(self, pitch):
      """Set the sequence's playback pitch, transposing the music to match.

      Args:
          pitch (int or float): The new playback pitch, as a MIDI pitch from 0 to 127.
      """
      try:
         pitch = int(pitch)   # convert to integer

      except Exception:
         return   # invalid pitch, so do nothing

      # calculate semitone difference from base pitch
      semitones = pitch - self.defaultPitch

      # update transpose for future notes only
      self._transposeSemitones = semitones   # remember transpose amount

   def getPitch(self):
      """Return the sequence's current playback pitch.

      Returns:
          currentPitch (int): The current playback pitch, as a MIDI pitch from 0 to 127.
      """
      currentPitch = self.defaultPitch + self._transposeSemitones   # calculate current pitch
      return currentPitch

   def getDefaultPitch(self):
      """Return the pitch the sequence was created with.

      Returns:
          defaultPitch (int): The default playback pitch, as a MIDI pitch from 0 to 127.
      """
      defaultPitch = self.defaultPitch
      return defaultPitch

   def setTempo(self, bpm):
      """Set the sequence's playback tempo.

      Args:
          bpm (int or float): The new tempo, in beats per minute.
      """
      bpm = float(bpm)   # convert to float
      if bpm > 0:   # is the tempo valid?
         self.tempoFactor = bpm / max(1e-9, self.defaultTempo)   # calculate tempo factor

   def getTempo(self):
      """Return the sequence's current playback tempo.

      Returns:
          tempo (int or float): The current tempo, in beats per minute.
      """
      tempo = self.defaultTempo * self.tempoFactor
      return tempo

   def getDefaultTempo(self):
      """Return the tempo the sequence was created with.

      Returns:
          defaultTempo (int or float): The default tempo, in beats per minute.
      """
      defaultTempo = self.defaultTempo
      return defaultTempo

   def setVolume(self, volume):
      """Set the sequence's playback volume, making it louder or softer.

      Args:
          volume (int): The new volume, from 0 (silent) to 127 (loudest).
      """
      try:
         volume = int(volume)   # convert to integer

      except Exception:
         return   # invalid volume, so do nothing

      self.volume = max(0, min(127, volume))   # clamp volume to valid MIDI range

   def getVolume(self):
      """Return the sequence's current playback volume.

      Returns:
          volume (int): The current volume, from 0 (silent) to 127 (loudest).
      """
      volume = self.volume
      return volume

   def _extractEvents(self, score):
      """"""
      events = []
      tempo = score.getTempo()   # get global tempo (can be overridden by part and phrase tempos)

      for part in score.getPartList():
         channel = part.getChannel()        # get part channel
         instrument = Play.getInstrument(channel)  # get global instrument for this channel

         if part.getInstrument() > -1:      # has the part instrument been set?
            instrument = part.getInstrument()  # yes, so it takes precedence

         partTempo = tempo
         if part.getTempo() > -1:           # has the part tempo been set?
            partTempo = part.getTempo()        # yes, so update tempo

         for phrase in part.getPhraseList():
            phraseInstrument = instrument
            phraseTempo = partTempo

            if phrase.getInstrument() > -1:        # is this phrase's instrument set?
               phraseInstrument = phrase.getInstrument()    # yes, so it takes precedence

            if phrase.getTempo() > -1:          # has the phrase tempo been set?
               phraseTempo = phrase.getTempo()           # yes, so update tempo

            # time factor to convert time from jMusic Score units to milliseconds
            # (this needs to happen here every time, as we may be using the tempo from score, part, or phrase)
            FACTOR = 1000 * 60.0 / phraseTempo   # beats → ms

            startTimeMs = phrase.getStartTime() * FACTOR   # in milliseconds
            noteList = phrase.getNoteList()

            for note in noteList:
               pitch = note.getPitch()

               if pitch == REST:   # skip rest notes
                  startTimeMs += note.getDuration() * FACTOR
                  continue

               # NOTE: Below we use note length as opposed to duration (getLength() vs. getDuration())
               # since note length gives us a more natural sounding note (with proper decay), whereas
               # note duration captures the more formal (printed score) duration (which sounds unnatural).
               lengthMs = int(note.getLength() * FACTOR)             # get note length (as opposed to duration!) and convert to milliseconds
               velocity = note.getDynamic()
               panning = mapValue(note.getPan(), 0.0, 1.0, 0, 127)    # map from range 0.0..1.0 (Note panning) to range 0..127 (as expected by Java synthesizer)

               startMs = int(startTimeMs)                           # remember this note's start time (in milliseconds)
               endMs = startMs + lengthMs

               events.append({
                  'startMs': startMs,
                  'endMs': endMs,
                  'pitch': pitch,
                  'velocity': velocity,
                  'channel': channel,
                  'instrument': phraseInstrument,
                  'panning': int(panning)
               })

               startTimeMs += note.getDuration() * FACTOR   # advance logical time

      # sort by start time to ensure correct order
      events.sort(key=lambda e: e['startMs'])
      return events

   def _tick(self):
      """"""
      if not self._playing:   # is the sequencer stopped?
         return               # yes, so do nothing

      # advance timeline according to tempo factor
      self._positionMs += self._tickIntervalMs * self.tempoFactor   # advance position
      pos = int(self._positionMs)

      # handle end of sequence first (before early exit)
      if self._positionMs >= self._totalDurationMs:   # have we reached the end?

         if self._loop and self._totalDurationMs > 0:   # should we loop?
            # wrap position and restart from beginning
            self._positionMs = 0.0   # reset to beginning
            self._nextEventIndex = 0   # restart from first event
            pos = 0   # update pos for the rest of the method
            # don't call stop() - continue playing

         else:
            # stop playback at end
            self.stop()   # stop the sequence
            return

      # early exit if no events to process
      if self._nextEventIndex >= self._numEvents:
         return

      # start any events whose start time has come
      while self._nextEventIndex < self._numEvents and self._events[self._nextEventIndex]['startMs'] <= pos:
         event = self._events[self._nextEventIndex]

         # pitch calculation (needed for real time pitch shifting)
         transPitch = event['pitch'] + self._transposeSemitones
         if transPitch < 0:
            transPitch = 0
         elif transPitch > 127:
            transPitch = 127

         # calculate remaining duration for this note
         remainingMs = max(0, event['endMs'] - pos)

         # scale this note's loudness by the sequence's overall volume (0 to 127),
         # so setVolume() can make the whole sequence louder or softer while it plays
         scaledVelocity = int(event['velocity'] * self.volume / 127)

         # use Play.note() which handles noteOn/noteOff automatically with proper timing
         Play.note(transPitch, 0, remainingMs, scaledVelocity, event['channel'], event['panning'])

         self._nextEventIndex += 1   # move to next event


####################################################################################
##### Read and Write ###############################################################
####################################################################################

# read a MIDI file into a Score using the Read.midi() function
class Read:
   """Read music into the library from external files.

   Read is a static utility. Call its methods on the class itself, for example
   Read.midi().
   """

   @staticmethod
   def midi(score, filename, humanize=False):
      """Read a MIDI file into a score, replacing the score's contents.

      Args:
          score (Score): The score to read the music into; its current contents are cleared.
          filename (str): The MIDI file to read (a .mid file).
          humanize (bool, optional): If True, give the notes their default sounding length (about 90% of their duration) for a more natural feel, instead of keeping the exact recorded timing.

      Returns:
          score (Score): The score, now holding the music from the file.
      """
      import mido      # MIDI file operations
      import os        # file path operations

      if score is None:
         print("Read.midi error: The score is not initialised! I'm doing it for you.")
         score = Score()

      score.empty()   # clear any existing data

      print("\n--------------------- Reading MIDI File ---------------------")

      # Relative paths resolve against cwd -- same convention as gui.Icon().
      try:
         midiFile = mido.MidiFile(filename)

         # set the score title to the filename (without extension)
         score.setTitle(os.path.splitext(os.path.basename(filename))[0])

         # process each track
         for trackIndex, track in enumerate(midiFile.tracks):
            part = Part()
            # part.setTitle(f"Track {trackIndex}") # Optional: name part by track index or name

            phrasesForPart = []
            # stores the logical end time for each phrase in phrasesForPart
            phraseCurrentLogicalEndTime = []

            activeNotesOnTrack = {}      # key=(channel, pitch), value=list of (startTime_ticks, velocity)
            absoluteTimeTicksTrack = 0   # cumulative time in ticks for the current track
            currentPanValue = 0.5   # track current pan (default = center, 0.0-1.0)

            for msg in track:
               absoluteTimeTicksTrack += msg.time

               if msg.type == 'program_change':
                  part.setInstrument(msg.program)
                  part.setChannel(msg.channel)

               elif msg.type == 'set_tempo':
                  tempoBpm = 60000000 / msg.tempo
                  score.setTempo(tempoBpm)

               elif msg.type == 'time_signature':
                  score.setTimeSignature(msg.numerator, msg.denominator)

               elif msg.type == 'key_signature':
                  # Map mido key strings to (keySignature, keyQuality)
                  # keySignature: num sharps (positive) or flats (negative)
                  # keyQuality: 0 = Major, 1 = Minor
                  midoKeySignatureMap = {
                     'C': (0, 0), 'Am': (0, 1),
                     'G': (1, 0), 'Em': (1, 1),
                     'D': (2, 0), 'Bm': (2, 1),
                     'A': (3, 0), 'F#m': (3, 1),
                     'E': (4, 0), 'C#m': (4, 1),
                     'B': (5, 0), 'G#m': (5, 1),
                     'F#': (6, 0), 'D#m': (6, 1),
                     'C#': (7, 0), 'A#m': (7, 1),
                     'F': (-1, 0), 'Dm': (-1, 1),
                     'Bb': (-2, 0), 'Gm': (-2, 1),
                     'Eb': (-3, 0), 'Cm': (-3, 1),
                     'Ab': (-4, 0), 'Fm': (-4, 1),
                     'Db': (-5, 0), 'Bbm': (-5, 1),
                     'Gb': (-6, 0), 'Ebm': (-6, 1),
                     'Cb': (-7, 0), 'Abm': (-7, 1)
                  }

                  if msg.key in midoKeySignatureMap:
                     signature, quality = midoKeySignatureMap[msg.key]
                     score.setKeySignature(signature)
                     score.setKeyQuality(quality)

               elif msg.type == 'control_change':
                  if msg.is_cc(7):   # volume controller
                     part.setVolume(msg.value)   # 0-127, no conversion needed
                  elif msg.is_cc(10):   # pan controller
                     currentPanValue = msg.value / 127.0   # MIDI 0-127 -> float 0.0-1.0

               elif msg.type == 'note_on' and msg.velocity > 0:   # note on
                  part.setChannel(msg.channel)
                  key = (msg.channel, msg.note)
                  if key not in activeNotesOnTrack:
                     activeNotesOnTrack[key] = []
                  activeNotesOnTrack[key].append( (absoluteTimeTicksTrack, msg.velocity) )

               elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):   # note off
                  key = (msg.channel, msg.note)
                  if key in activeNotesOnTrack and activeNotesOnTrack[key]:
                     startTimeTicks, velocity = activeNotesOnTrack[key].pop(0)
                     if not activeNotesOnTrack[key]:   # clean up if list is empty
                        del activeNotesOnTrack[key]

                     noteStartTime = startTimeTicks / midiFile.ticks_per_beat
                     noteEndTime = absoluteTimeTicksTrack / midiFile.ticks_per_beat

                     if noteEndTime <= noteStartTime:
                        continue

                     duration = noteEndTime - noteStartTime

                     targetPhraseIndex = -1
                     for phraseIdx in range(len(phrasesForPart)):
                        # A phrase is suitable if this note starts at or after the phrase's current logical end time
                        # (with a small tolerance for notes that might slightly precede the 'official' end due to rounding)
                        # jMusic uses a 0.08 beat tolerance.
                        if phraseCurrentLogicalEndTime[phraseIdx] <= noteStartTime + 0.08:
                           targetPhraseIndex = phraseIdx
                           break

                     # create new phrase if no suitable existing phrase found
                     if targetPhraseIndex == -1:
                        newPhrase = Phrase()
                        newPhrase.setStartTime(noteStartTime)
                        phrasesForPart.append(newPhrase)
                        phraseCurrentLogicalEndTime.append(noteStartTime)
                        targetPhraseIndex = len(phrasesForPart) - 1

                     # get reference to current phrase and its logical end time
                     currentSelectedPhrase = phrasesForPart[targetPhraseIndex]
                     currentPhraseLogicalEnd = phraseCurrentLogicalEndTime[targetPhraseIndex]

                     # add rest if there's a gap between current phrase end and note start
                     if noteStartTime > currentPhraseLogicalEnd:
                        restDuration = noteStartTime - currentPhraseLogicalEnd

                        # add explicit rest for gaps > 0.01 beats (ignore tiny gaps from MIDI timing jitter)
                        if restDuration > 0.01:
                           restNote = Note(REST, restDuration)
                           currentSelectedPhrase.addNote(restNote)
                           phraseCurrentLogicalEndTime[targetPhraseIndex] += restDuration

                     # create Note object
                     if humanize:   # optional humanize param
                        # don't explicitly set length, so length will be:
                        # duration * DEFAULT_LENGTH_MULTIPLIER
                        jmusicNote = Note(msg.note, duration, velocity)
                        # NOTE: this is intended to "humanize"
                        # the playback in Play.midi.

                     else:   # default behavior
                        # preserve exact MIDI playback: length = duration
                        jmusicNote = Note(msg.note, duration, velocity, length=duration)

                     jmusicNote.setPan(currentPanValue)   # apply current pan from CC 10
                     currentSelectedPhrase.addNote(jmusicNote)   # add note
                     phraseCurrentLogicalEndTime[targetPhraseIndex] = noteEndTime  # and update phrase end time
            # end of message loop for track

            # add all phrases to the part
            for createdPhrase in phrasesForPart:
               if createdPhrase.getNoteList():
                  part.addPhrase(createdPhrase)

            # add part if it has phrases or an instrument was set
            if part.getPhraseList() or part.getInstrument() != -1:
               score.addPart(part)
         # end of track loop

         print(f"MIDI file '{filename}' read into score '{score.getTitle()}'")

      except FileNotFoundError:   # file not found
         print(f"Read.midi error: File not found - {filename}")

      except Exception as e:   # catch any other errors
         print(f"Read.midi error: Could not read MIDI file '{filename}'.")
         print(f"Error details: {e}")

      print("-------------------------------------------------------------")

      # return score, whether modified or new
      return score


# write a MIDI file from a Score, Part, Phrase, or Note using the Write.midi() function
class Write:
   """Write music from the library out to external files.

   Write is a static utility. Call its methods on the class itself, for example
   Write.midi().
   """

   @staticmethod
   def midi(material, filename):
      """Write music library material to a MIDI file.

      If the file already exists, it is overwritten.

      Args:
          material (Note, Phrase, Part, or Score): The music to write.
          filename (str): The MIDI file to write (a .mid file).
      """
      import mido   # MIDI file operations
      import os     # file path operations

      # filename is a disk path when it's a string; otherwise treat it as a
      # writable file-like (mido.MidiFile.save understands both, but we also
      # need to gate the human-readable progress chatter on the disk path).
      writeToDisk = isinstance(filename, (str, os.PathLike))
      _log = print if writeToDisk else (lambda *args, **kwargs: None)

      # start timing and print header
      _log("\n----------------------------- Writing MIDI File ------------------------------")

      # do necessary datatype wrapping
      if isinstance(material, Note):
         material = Phrase(material)
      if isinstance(material, Phrase):   # no elif - we need to successively wrap from Note to Score
         material = Part(material)
         material.setInstrument(-1)     # indicate no default instrument (needed to access global instrument)
      if isinstance(material, Part):     # no elif - we need to successively wrap from Note to Score
         material = Score(material)

      if isinstance(material, Score):
         # we are good - let's write it then!
         score = material   # by now, material is a score, so create an alias (for readability)

         # create a new MIDI file (type 1) with 480 ticks per beat (standard)
         midiFile = mido.MidiFile(type=1, ticks_per_beat=480)

         # create a metadata track (track 0) for global info
         metaTrack = mido.MidiTrack()
         midiFile.tracks.append(metaTrack)

         # add score title to metadata track
         if score.getTitle():
            metaTrack.append(mido.MetaMessage('track_name', name=score.getTitle(), time=0))

         # add global tempo to metadata track
         microsecondsPerBeat = int(60000000 / score.getTempo())
         metaTrack.append(mido.MetaMessage('set_tempo', tempo=microsecondsPerBeat, time=0))

         # add time signature to metadata track
         if hasattr(score, 'getNumerator') and hasattr(score, 'getDenominator'):
            numerator = score.getNumerator()
            denominator = score.getDenominator()
            metaTrack.append(mido.MetaMessage('time_signature',
                                              numerator=numerator,
                                              denominator=denominator,
                                              time=0))

         # add key signature to metadata track
         # reverse mapping from (keySignature, keyQuality) to mido key strings
         reverseKeySignatureMap = {
            (0, 0): 'C', (0, 1): 'Am',
            (1, 0): 'G', (1, 1): 'Em',
            (2, 0): 'D', (2, 1): 'Bm',
            (3, 0): 'A', (3, 1): 'F#m',
            (4, 0): 'E', (4, 1): 'C#m',
            (5, 0): 'B', (5, 1): 'G#m',
            (6, 0): 'F#', (6, 1): 'D#m',
            (7, 0): 'C#', (7, 1): 'A#m',
            (-1, 0): 'F', (-1, 1): 'Dm',
            (-2, 0): 'Bb', (-2, 1): 'Gm',
            (-3, 0): 'Eb', (-3, 1): 'Cm',
            (-4, 0): 'Ab', (-4, 1): 'Fm',
            (-5, 0): 'Db', (-5, 1): 'Bbm',
            (-6, 0): 'Gb', (-6, 1): 'Ebm',
            (-7, 0): 'Cb', (-7, 1): 'Abm'
         }

         keySignature = score.getKeySignature()   # -7 to 7
         keyQuality = score.getKeyQuality()   # 0=Major, 1=Minor
         keyTuple = (keySignature, keyQuality)

         if keyTuple in reverseKeySignatureMap:
            midoKeyString = reverseKeySignatureMap[keyTuple]
            metaTrack.append(mido.MetaMessage('key_signature', key=midoKeyString, time=0))

         # end of metadata track
         metaTrack.append(mido.MetaMessage('end_of_track', time=0))

         # handle each part in the score
         for partIndex, part in enumerate(score.getPartList()):
            # print part information
            partTitle = part.getTitle() if part.getTitle() else ""
            _log(f"    Part {partIndex} '{partTitle}' to Track on Ch. {part.getChannel()}: ", end="")

            # create a new track for this part
            track = mido.MidiTrack()
            midiFile.tracks.append(track)

            # set track name to the part's title
            trackName = part.getTitle() if part.getTitle() else f"Track {partIndex}"
            track.append(mido.MetaMessage('track_name', name=trackName, time=0))

            # set part-specific tempo if it differs from the score's tempo
            partTempo = part.getTempo()
            if partTempo > 0 and partTempo != score.getTempo():
               microsecondsPerBeat = int(60000000 / partTempo)
               track.append(mido.MetaMessage('set_tempo', tempo=microsecondsPerBeat, time=0))

            # set instrument via program change
            instrument = part.getInstrument()
            if instrument >= 0:
               track.append(mido.Message('program_change',
                                       program=instrument,
                                       channel=part.getChannel(),
                                       time=0))

            # set track volume (CC 7)
            volume = part.getVolume()
            if volume >= 0:
               track.append(mido.Message('control_change',
                                          control=7,  # volume controller
                                          value=volume,
                                          channel=part.getChannel(),
                                          time=0))

            # collect all notes from all phrases
            events = []

            for phraseIndex, phrase in enumerate(part.getPhraseList()):
               dotCount = phrase.getSize()
               _log(f" Phrase {phraseIndex}:" + "." * dotCount, end="")

               # get phrase start time in ticks
               phraseStartTicks = int(phrase.getStartTime() * 480)

               # apply phrase instrument if set
               phraseInstrument = phrase.getInstrument()
               if phraseInstrument >= 0:
                  events.append({
                     'tick': phraseStartTicks,
                     'msg': mido.Message('program_change',
                                       program=phraseInstrument,
                                       channel=part.getChannel(),
                                       time=0)
                  })

               # apply phrase tempo if set
               phraseTempo = phrase.getTempo()
               if phraseTempo > 0:
                  phraseMicrosecondsPerBeat = int(60000000 / phraseTempo)
                  events.append({
                     'tick': phraseStartTicks,
                     'msg': mido.MetaMessage('set_tempo',
                                          tempo=phraseMicrosecondsPerBeat,
                                          time=0)
                  })

               # process each note in the phrase
               for noteIndex in range(phrase.getSize()):
                  note = phrase.getNote(noteIndex)

                  # get note parameters
                  pitch = note.getPitch()

                  # skip rests
                  if pitch < 0:
                     continue

                  # convert note timing to ticks
                  noteStartTime = phrase.getNoteStartTime(noteIndex)
                  noteTicks = phraseStartTicks + int(noteStartTime * 480)

                  # calculate note duration in ticks
                  # NOTE: we use getDuration() to preserve the exact notated timing
                  soundingTicks = int(note.getDuration() * 480)

                  # get note velocity (dynamic)
                  velocity = note.getDynamic()

                  # get note pan (0.0-1.0) and convert to MIDI (0-127)
                  pan = note.getPan()
                  midiPan = int(pan * 127)
                  events.append({
                     'tick': noteTicks,
                     'msg': mido.Message('control_change',
                                       control=10,  # pan controller
                                       value=midiPan,
                                       channel=part.getChannel(),
                                       time=0)
                  })

                  # create note_on event
                  events.append({
                     'tick': noteTicks,
                     'msg': mido.Message('note_on',
                                       note=pitch,
                                       velocity=velocity,
                                       channel=part.getChannel(),
                                       time=0)
                  })

                  # create note_off event
                  events.append({
                     'tick': noteTicks + soundingTicks,
                     'msg': mido.Message('note_off',
                                       note=pitch,
                                       velocity=0,
                                       channel=part.getChannel(),
                                       time=0)
                  })

            # sort events by tick
            events.sort(key=lambda event: event['tick'])

            # convert absolute ticks to delta ticks
            previousTick = 0
            for event in events:
               deltaTicks = event['tick'] - previousTick
               event['msg'].time = deltaTicks
               previousTick = event['tick']
               track.append(event['msg'])

            # end of track
            track.append(mido.MetaMessage('end_of_track', time=0))

            _log() # newline after processing all phrases for a part

         # save the MIDI file. With a disk path we normalize the .mid extension
         # and print where it landed; with a file-like target we hand the buffer
         # straight to mido and skip the cosmetic chatter.
         if writeToDisk:
            if not filename.lower().endswith('.mid'):
               filename += '.mid'
            midiFile.save(filename)
            print(f"MIDI file '{os.path.abspath(filename)}' written from score '{score.getTitle()}'.")
            print("------------------------------------------------------------------------------\n")
         else:
            midiFile.save(file=filename)

      else:   # error check
         print(f'Write.midi(): Unrecognized type {type(material)}, expected Note, Phrase, Part, or Score.')


#######################################################################################
##### Metronome #######################################################################
#######################################################################################

#from gui import Display     # for Metronome tick visualization

# used to keep track which Metronome objects are active
_activeMetronomes = []     # holds active MidiSequence objects

class Metronome():
   """Keep time and call functions on the beat, at a set tempo and time signature.

   A metronome schedules your functions to run on chosen beats. This is handy for starting
   blocks of music together, though it can drive anything. Add functions with add(), then
   start() the metronome.

   Args:
       tempo (int, optional): The tempo, in beats per minute.
       timeSignature (list[int], optional): The time signature as [beats, beatValue], for example [4, 4] for 4/4.
   """

   #def __init__(self, tempo=60, timeSignature=[4, 4], displaySize=50, displayTickColor=Color.RED):
   def __init__(self, tempo=60, timeSignature=[4, 4]):

      # remember title, tempo and time signature
      self.tempo = tempo
      self.timeSignature = timeSignature  # a list (first item is numerator, second is denominator)

      # list of actions (we are asked to synchronize) and their information (parallel lists)
      self.actions          = []    # functions to call
      self.parameters       = []    # their corresponding parameters
      self.desiredBeats     = []    # on which beat to call them (0 means now)
      self.repeatFlags      = []    # if they are meant to be called repeatedly
      self.beatCountdowns   = []    # holds beat countdown until call

      # create timer, upon which to base our operation
      delay = int((60.0 / self.tempo) * 1000)   # in milliseconds
      self.timer = Timer(delay, self._callActions, [], True)

      # set up metronome visualization
#      self.display = Display("Metronome", displaySize, displaySize+20, 0, 0)
#      self.display.hide()      # initially hidden
#
#      # set up display ticking
#      self.displayTickColor = displayTickColor               # color used for ticking
#      self.displayOriginalColor = self.display.getColor()    # color to reset ticking
#      self.flickerTimer = Timer(100, self.display.setColor, [self.displayOriginalColor])   # create timer to reset display color (it ends fliker)
#      self.add( self.__updateDisplay__, [], 0, True, 1)      # schedule display flickering on every beat (starts flicker)

      # set up metronome visualization / sonification
      self.currentBeat   = 1       # holds current beat relative to provided time signature (1 means first beat)
      self.visualize     = False   # True means print out current beat on console; False do not print
      self.sonify        = False   # True means sound each tick; False do not
      self.sonifyPitch   = HI_MID_TOM   # which pitch to play whe ticking
      self.sonifyChannel = 9       # which channel to use (9 is for percussion)
      self.sonifyVolume  = 127     # how loud is strong beat (secondary beats will at 70%)

      # remember that this MidiSequence has been created and is active (so that it can be stopped by JEM, if desired)
      _activeMetronomes.append(self)

   def __str__(self):
      return f'Metronome(tempo = {self.tempo}, timeSignature = {self.timeSignature})'

   def __repr__(self):
      return str(self)

   def add(self, action, parameters=[], desiredBeat=0, repeatFlag=False):
      """Schedule a function for the metronome to call on a given beat.

      Args:
          action (Callable): The function to call.
          parameters (list, optional): The parameters to pass to the function.
          desiredBeat (int, optional): Which beat to call it on. 0 means the very next beat, 1 the first beat of the measure, 2 the second, and so on. A beat past the end of the measure carries into later measures.
          repeatFlag (bool, optional): Whether to call it every time that beat comes around (True) or just once (False).
      """
      self.actions.append( action )
      self.parameters.append( parameters )
      self.desiredBeats.append( desiredBeat )
      self.repeatFlags.append( repeatFlag )

      # calculate beat countdown
      beatCountdown = self._calculateBeatCountdown( desiredBeat )

      # store beat countdown for this action
      self.beatCountdowns.append( beatCountdown )

   def remove(self, action):
      """Remove a scheduled function from the metronome.

      If the function was scheduled several times, the earliest one is removed; call again to
      remove more.

      Args:
          action (Callable): The function to remove.
      """
      index = self.actions.index( action )   # find index of leftmost occurrence
      self.actions.pop( index )                # and remove it and all info
      self.parameters.pop( index )
      self.desiredBeats.pop( index )
      self.repeatFlags.pop( index )
      self.beatCountdowns.pop( index )

   def removeAll(self):
      """Remove every scheduled function from the metronome.
      """
      # reinitialize all action related information
      self.actions        = []
      self.parameters       = []
      self.desiredBeats     = []
      self.repeatFlags      = []
      self.beatCountdowns   = []

   def setTempo(self, tempo):
      """Set the metronome's tempo.

      Args:
          tempo (int or float): The new tempo, in beats per minute.
      """
      self.tempo = tempo        # remember new tempo

      # and set it
      delay = int((60.0 / self.tempo) * 1000)   # in milliseconds
      self.timer.setDelay(delay)

   def getTempo(self):
      """Return the metronome's tempo.

      Returns:
          tempo (int or float): The tempo, in beats per minute.
      """
      tempo = self.tempo
      return tempo

   def setTimeSignature(self, timeSignature):
      """Set the metronome's time signature.

      Args:
          timeSignature (list[int]): The time signature as [beats, beatValue], for example [4, 4] for 4/4.
      """
      self.timeSignature = timeSignature        # remember new time signature
      self.currentBeat = 0                      # reinitialize current beat relative to provided time signature (1 means first beat)

   def getTimeSignature(self):
      """Return the metronome's time signature.

      Returns:
          timeSignature (list[int]): The time signature as [beats, beatValue], for example [4, 4] for 4/4.
      """
      timeSignature = self.timeSignature
      return timeSignature

   def start(self):
      """Start the metronome ticking.
      """
      self.timer.start()
      #print("Metronome started...")

   def stop(self):
      """Stop the metronome ticking.
      """
      self.timer.stop()
      #print("Metronome stopped.")

#   def __updateDisplay__(self):
#      not nstanceIt) temporarily flickers the metronome's visualization display to indicate a 'tick'."""
#
#      # change color to indicate a tick
#      self.display.setColor( self.displayTickColor )
#
#      # reset display back to original color after a small delay
#      #flikcerTimer = Timer(250, self.display.setColor, [self.displayOriginalColor])
#      #flikcerTimer.start()    # after completion, this timer will eventually be garbage collected (no need to reuse)
#      self.flickerTimer.start()

#   def __advanceCurrentBeat__(self):
#      """It advances the current metronome beat."""
#
#      if self.visualize:   # do we need to print out current beat?
#         print(self.currentBeat)
#
#      if self.sonify:   # do we need to sound out current beat?
#         if self.currentBeat == 1:    # strong (first) beat?
#            Play.note(self.sonifyPitch, 0, 200, self.sonifyVolume, self.sonifyChannel)   # louder
#         else:
#            Play.note(self.sonifyPitch, 0, 200, int(self.sonifyVolume * 0.7), self.sonifyChannel)   # softer
#
#      self.currentBeat = (self.currentBeat % self.timeSignature[0]) + 1  # wrap around as needed

   def _callActions(self):
      """"""
      # do visualization / sonification tasks (if any)
      if self.visualize:   # do we need to print out current beat?
         print(self.currentBeat)

      if self.sonify:   # do we need to sound out current beat?
         if self.currentBeat == 1:    # strong (first) beat?
            Play.note(self.sonifyPitch, 0, 200, self.sonifyVolume, self.sonifyChannel)   # louder
         else:
            Play.note(self.sonifyPitch, 0, 200, int(self.sonifyVolume * 0.7), self.sonifyChannel)   # softer

      # NOTE:  The following uses several for loops so that all actions are given quick service.
      #        Once they've been called, we can loop again to do necessary book-keeping...

      # first, iterate to call all actions with their (provided) parameters
      nonRepeatedActions = []   # holds indices of actions to be called only once (so we can remove them later)
      for i in range( len(self.actions) ):

         # see if current action needs to be called right away
         if self.beatCountdowns[i] == 0:

            # yes, so call this action!!!
            self.actions[i]( *(self.parameters[i]) )   # strange syntax, but does the trick...

            # check if action was meant to be called only once, and if so remove from future consideration
            if not self.repeatFlags[i]:  # call only once?

               nonRepeatedActions.append( i )   # mark it for deletion (so it is not called again)

      # now, all actions who needed to be called have been called

      # next, iterate to remove any actions that were meant to be called once
      # NOTE: We remove actions right-to-left - see use of reversed().  This way, as lists shrink,
      #       we can still find earlier items to be removed!!!
      for i in reversed(nonRepeatedActions):
         self.actions.pop( i )
         self.parameters.pop( i )
         self.desiredBeats.pop( i )
         self.repeatFlags.pop( i )
         self.beatCountdowns.pop( i )


      ###########################################################################################
      # NOTE:  This belongs exactly here (before updating countdown timers below)

      # advance to next beat (in anticipation...)
      self.currentBeat = (self.currentBeat % self.timeSignature[0]) + 1  # wrap around as needed

      ###########################################################################################

      # finally, iterate to update countdown timers for all remaining actions
      for i in range( len(self.actions) ):

         # if this action was just called
         if self.beatCountdowns[i] == 0:

            # reinitialize its beat countdown counter, i.e., reschedule it for its next call

            # calculate beat countdown
            self.beatCountdowns[i] = self._calculateBeatCountdown( self.desiredBeats[i] )

         else:   # it's not time to call this action, so update its information

            # reduce ticks remaining to call it
            self.beatCountdowns[i] = self.beatCountdowns[i] - 1     # we are now one tick closer to calling it

      # now, all actions who needed to be called have been called, and all beat countdowns
      # have been updated.

   def _calculateBeatCountdown(self, desiredBeat):
      """"""
      if desiredBeat == 0:  # do they want now (regardess of current beat)?
         beatCountdown = 0     # give them now
      elif self.currentBeat <= desiredBeat <= self.timeSignature[0]:  # otherwise, is desired beat the remaining measure?
         beatCountdown = desiredBeat - self.currentBeat                            # calculate remaining beats until then
      elif 1 <= desiredBeat < self.currentBeat:                       # otherwise, is desired beat passed in this measure?
         beatCountdown = (desiredBeat + self.timeSignature[0]) - self.currentBeat  # pick it up in the next measure
      elif self.timeSignature[0] < desiredBeat:                       # otherwise, is desired beat beyond this measure?
         beatCountdown = desiredBeat - self.currentBeat + self.timeSignature[0]    # calculate remaining beats until then
      else:  # we cannot handle negative beats
         raise ValueError("Cannot handle negative beats, " + str(desiredBeat) + ".")

      return beatCountdown

   def show(self):
      """Start printing the current beat number to the console on each tick.
      """
      #self.display.show()
      self.visualize = True

   def hide(self):
      """Stop printing the beat number to the console.
      """
      #self.display.hide()
      self.visualize = False

   def soundOn(self, pitch=ACOUSTIC_BASS_DRUM, volume=127, channel=9):
      """Play a sound on every metronome tick.

      The strong (first) beat of each measure sounds at the given volume; the other beats
      sound softer (about 70% as loud).

      Args:
          pitch (int, optional): The pitch to play on each tick, as a MIDI pitch.
          volume (int, optional): How loud the strong beat is, from 0 to 127.
          channel (int, optional): The channel to play on, from 0 to 15; channel 9 is the percussion channel.
      """
      self.sonify = True
      self.sonifyPitch   = pitch   # which pitch to play whe ticking
      self.sonifyChannel = channel # which channel to use (9 is for percussion)
      self.sonifyVolume  = volume  # how loud is strong beat (secondary beats will at 70%)

   def soundOff(self):
      """Stop playing a sound on each metronome tick.
      """
      self.sonify = False


#######################################################################################
##### View ############################################################################
#######################################################################################

# create visual representations of Scores, Parts, or Phrases
class View:
   """Show or print music library material in different ways.

   View is a static utility. Call its methods on the class itself, for example
   View.pianoRoll().
   """

   @staticmethod
   def pianoRoll(material):
      """Show the music as a piano-roll display.

      Args:
          material (Phrase, Part, or Score): The music to show.
      """
      if type(material) not in (Score, Part, Phrase):
         print("View.pianoRoll: material must be a Score, Part, or Phrase.")
         return

      # Lazy imports keep View.pianoRoll cheap when it's never called.  
      # `gui` spawns the renderer subprocess on first touch, which
      # we don't want to incur unless a pianoRoll is made.
      import io
      import os
      import tempfile
      import warnings
      import mido
      import numpy as np
      from pretty_midi import PrettyMIDI
      import pypianoroll
      from matplotlib.figure import Figure
      from matplotlib.backends.backend_agg import FigureCanvasAgg
      from gui import Display, Icon

      # Write the score into an in-memory MIDI buffer (no temp file on disk),
      # then re-parse it with mido + pretty_midi so pypianoroll can produce
      # the per-track pianoroll matrices.
      buffer = io.BytesIO()
      Write.midi(material, buffer)
      buffer.seek(0)

      with warnings.catch_warnings():
         # pretty_midi complains about meta events on non-zero tracks; that's
         # how Write.midi structures a multi-track file, and the warning isn't
         # actionable for end users.
         warnings.filterwarnings(
            "ignore",
            message="Tempo, Key or Time signature change events.*",
            category=RuntimeWarning,
            module=r"pretty_midi",
         )
         midoFile   = mido.MidiFile(file=buffer)
         prettyMidi = PrettyMIDI(mido_object=midoFile)
         multitrack = pypianoroll.from_pretty_midi(prettyMidi)

      # Per-track plot inputs: pianoroll matrix, used pitch range, pitch labels.
      pitchNames = ["C", "Db", "D", "Eb", "E", "F", "Gb", "G", "Ab", "A", "Bb", "B"]

      tracks = []
      for track in multitrack.tracks:
         pianoroll = np.asarray(track.pianoroll)
         hasNote   = pianoroll.any(axis=0)
         if not np.any(hasNote):
            continue   # skip silent tracks rather than render a blank subplot

         pitches   = np.where(hasNote)[0]
         lowPitch  = int(pitches[0])
         highPitch = int(pitches[-1])
         pitchLabels = [f"{pitchNames[pitch % 12]}{(pitch // 12) - 1}"
                        for pitch in range(lowPitch, highPitch + 1)]
         tracks.append((pianoroll, lowPitch, highPitch, pitchLabels))

      if not tracks:
         print("View.pianoRoll: material contains no notes to plot.")
         return

      # Convert midi data to a matplotlib figure: time-scaled width, and
      # per-track height tall enough to keep one pitch-label per row without
      # vertical overlap.  Capped so very long material doesn't blow up RAM.
      nTracks      = len(tracks)
      maxTimeSteps = max(pianoroll.shape[0] for pianoroll, _, _, _ in tracks)
      maxRange     = max(highPitch - lowPitch + 2 for _, lowPitch, highPitch, _ in tracks)
      pxPerStep    = 2
      pxPerPitch   = 14   # ~ default matplotlib tick-label line height
      imageWidth   = max(800, min(int(maxTimeSteps * pxPerStep), 4096))
      imageHeight  = max(200, nTracks * (maxRange * pxPerPitch + 30))

      dpi    = 100
      figure = Figure(figsize=(imageWidth / dpi, imageHeight / dpi), dpi=dpi)
      FigureCanvasAgg(figure)

      if nTracks == 1:
         axes = [figure.add_subplot(111)]
      else:
         axes = list(figure.subplots(nTracks, 1, sharex=True))
         figure.subplots_adjust(hspace=0)

      defaultCmaps = ("Blues", "Oranges", "Greens", "Reds", "Purples", "Greys")

      for index, (ax, (pianoroll, lowPitch, highPitch, pitchLabels)) in enumerate(zip(axes, tracks)):
         cmap = defaultCmaps[index % len(defaultCmaps)]
         # Mask empty cells so the colormap's zero color doesn't paint over the
         # gridlines underneath; masked cells render transparent by default.
         # zorder=1 lifts the data bars above the gridlines (axisbelow puts
         # the grid at zorder 0.5), so the grid appears only in empty areas.
         maskedRoll = np.ma.masked_where(pianoroll == 0, pianoroll)
         ax.imshow(maskedRoll.T, cmap=cmap, aspect="auto",
                   vmin=0, vmax=127, origin="lower", interpolation="none",
                   zorder=1)
         ax.set_ylim(lowPitch - 1, highPitch + 1)
         ax.set_yticks(np.arange(lowPitch, highPitch + 1, dtype=int))
         ax.set_yticklabels(pitchLabels)
         # Gridlines on the major ticks land at row centers; axisbelow keeps
         # the grid behind imshow.
         ax.grid(axis='y', which='major', color='lightgray', linewidth=0.5)
         ax.set_axisbelow(True)
         ax.set_xlabel('')
         ax.set_ylabel('')
         ax.tick_params(axis='x', which='both', labelbottom=False, labelleft=False)

      figure.tight_layout()

      # Convert matplotlib figure to PNG for Icon()
      fd, tempPath = tempfile.mkstemp(suffix='.png')
      os.close(fd)
      try:
         figure.savefig(tempPath, dpi=dpi)

         maxDisplayWidth, maxDisplayHeight = 1280, 720
         displayWidth  = min(imageWidth,  maxDisplayWidth)
         displayHeight = min(imageHeight, maxDisplayHeight)

         display = Display("Piano Roll", width=displayWidth, height=displayHeight)

         if imageWidth > displayWidth or imageHeight > displayHeight:
            # make Display scrollable if image is too large
            display._setScrollable(imageWidth, imageHeight)

         icon = Icon(tempPath)   # width=None forces a sync query; renderer has read the file by then
         display.add(icon, 0, 0)

      finally:
         # cleanup - release the temp file
         os.unlink(tempPath)

   @staticmethod
   def sketch(material):
      """Show the music as a small piano-roll display.

      Args:
          material (Note, Phrase, Part, or Score): The music to show.
      """
      from gui import Display, Color

      # do necessary datatype wrapping
      if isinstance(material, Note):
         material = Phrase(material)
      if isinstance(material, Phrase):   # no elif - we need to successively wrap from Note to Score
         material = Part(material)
      if isinstance(material, Part):     # no elif - we need to successively wrap from Note to Score
         material = Score(material)
      if isinstance(material, Score):
         # we are good - let's sketch it!
         score = material   # by now, material is a score, so create an alias (for readability)

         # constants for dynamic width scaling
         DEFAULT_DISPLAY_WIDTH = 600
         DEFAULT_DISPLAY_HEIGHT = 400
         REFERENCE_DURATION_SCORE_UNITS = 32.0   # 32 quarter notes (8 measures of 4/4)
         SCREEN_MARGIN_PIXELS = 20
         MIN_DISPLAY_WIDTH = 400

         # assign colors to channels (ordered by visual appeal, most commonly used first)
         colorPalette = [
            Color(65, 105, 225),    # royal blue
            Color(34, 139, 34),     # forest green
            Color(220, 20, 60),     # crimson
            Color(255, 140, 0),     # dark orange
            Color(138, 43, 226),    # blue violet
            Color(0, 206, 209),     # dark turquoise
            Color(255, 20, 147),    # deep pink
            Color(184, 134, 11),    # dark goldenrod
            Color(46, 139, 87),     # sea green
            Color(178, 34, 34),     # firebrick
            Color(255, 99, 71),     # tomato
            Color(72, 61, 139),     # dark slate blue
            Color(210, 105, 30),    # chocolate
            Color(199, 21, 133),    # medium violet red
            Color(47, 79, 79),      # dark slate gray
            Color(0, 0, 0)          # black
         ]

         # loop through all parts and phrases to get all notes
         noteList = []               # holds all notes
         tempo = score.getTempo()    # get global tempo (can be overidden by part and phrase tempos)
         partNum = 0                 # used to assign colors
         totalDurationMs = 0           # used to scale x axis of sketch
         totalDurationScoreUnits = 0   # track duration in score units (tempo-independent)
         for part in score.getPartList():   # traverse all parts
            partEndTimeMs = 0   # track the end time of the longest phrase in this part
            partEndTimeScoreUnits = 0   # track part end time in score units
            channel = part.getChannel()        # get part channel

            # assign unique color to each part
            partColor = colorPalette[partNum % len(colorPalette)]
            partNum += 1

            if part.getTempo() > -1:           # has the part tempo been set?
               tempo = part.getTempo()            # yes, so update tempo
            for phrase in part.getPhraseList():   # traverse all phrases in part
               if phrase.getTempo() > -1:          # has the phrase tempo been set?
                  tempo = phrase.getTempo()           # yes, so update tempo

               # time factor to convert time from jMusic Score units to milliseconds
               # (this needs to happen here every time, as we may be using the tempo from score, part, or phrase)
               FACTOR = 1000 * 60.0 / tempo

               # process notes in this phrase
               startTime = phrase.getStartTime() * FACTOR   # in milliseconds
               phraseEndTimeMs = startTime   # track where this phrase ends
               startTimeScoreUnits = phrase.getStartTime()   # score units (before FACTOR)
               phraseEndTimeScoreUnits = startTimeScoreUnits
               for note in phrase.getNoteList():
                  start = int(startTime)                           # remember this note's start time (in milliseconds)

                  # NOTE:  Below we use note length as opposed to duration (getLength() vs. getDuration())
                  # since note length gives us a small gap between the sketch lines, whereas
                  # note duration captures the more formal duration which would connect the lines.
                  length = int(note.getLength() * FACTOR)             # get note length (as oppposed to duration!) and convert to milliseconds
                  startTime = startTime + note.getDuration() * FACTOR   # update start time (in milliseconds)
                  phraseEndTimeMs = startTime   # update phrase end time
                  # track position in score units (tempo-independent)
                  startTimeScoreUnits = startTimeScoreUnits + note.getDuration()   # no FACTOR
                  phraseEndTimeScoreUnits = startTimeScoreUnits
                  velocity = note.getDynamic()

                  pitch = note.getPitch()
                  # accumulate non-REST notes
                  if (pitch != REST):
                     # TODO: remove unecessary attributes from notelist
                     noteList.append((start, length, pitch, partColor))   # put start time first and duration second, so we can sort easily by start time (below),
                     # and so that notes that are members of a chord as denoted by having a duration of 0 come before the note that gives the specified chord duration

               # update part end time to be the maximum of all phrase end times
               partEndTimeMs = max(partEndTimeMs, phraseEndTimeMs)
               partEndTimeScoreUnits = max(partEndTimeScoreUnits, phraseEndTimeScoreUnits)

            # now, we finished parsing a Part, so check if it has the longest duration
            totalDurationMs = max(totalDurationMs, partEndTimeMs)
            totalDurationScoreUnits = max(totalDurationScoreUnits, partEndTimeScoreUnits)

         # now, the whole Score has been parsed
         # noteList is complete, and totalDurationMs is accurate

         # calculate optimal display width based on score duration (in score units, tempo-independent)
         MAX_DISPLAY_WIDTH = 1400   # reasonable cap for most monitors
         maxDisplayWidth = MAX_DISPLAY_WIDTH - SCREEN_MARGIN_PIXELS

         # calculate ideal width to maintain default scale (pixels per score unit)
         defaultScale = DEFAULT_DISPLAY_WIDTH / REFERENCE_DURATION_SCORE_UNITS
         idealWidth = int(totalDurationScoreUnits * defaultScale)

         # determine actual display width
         if idealWidth <= DEFAULT_DISPLAY_WIDTH:
            displayWidth = DEFAULT_DISPLAY_WIDTH   # short scores use default width
         elif idealWidth <= maxDisplayWidth:
            displayWidth = idealWidth   # expand to ideal width for medium scores
         else:
            displayWidth = maxDisplayWidth   # cap at monitor width for long scores

         # enforce minimum width
         displayWidth = max(displayWidth, MIN_DISPLAY_WIDTH)
         DISPLAY_WIDTH = displayWidth   # set for use in coordinate mapping
         DISPLAY_HEIGHT = DEFAULT_DISPLAY_HEIGHT

         # create a Display for the sketch (now with calculated width)
         display = Display(title="Sketch", width=DISPLAY_WIDTH, height=DISPLAY_HEIGHT)

         def msToXCoordinate(ms):
            # map from ms to display width
            xCoordinate = mapValue(ms, 0, totalDurationMs, 0, DISPLAY_WIDTH)
            return xCoordinate

         def midiPitchToYCoordinate(pitch):
            # map from midi pitch (0-127) to display height
            inverseY = mapValue(pitch, 0, 127, 0, DISPLAY_HEIGHT)
            yCoordinate = DISPLAY_HEIGHT - inverseY
            return yCoordinate

         # sort notes by start time
         noteList.sort()

         # sketch all notes in noteList
         chordNotes = []      # used to process notes belonging in a chord
         for start, length, pitch, partColor in noteList:
            # handle chord (if any)
            # Chords are denoted by a sequence of notes having the same start time and 0 duration (except the last note
            # of the chord).
            if length == 0:   # does this note belong in a chord?
               chordNotes.append([start, length, pitch])  # add it to the list of chord notes

            elif chordNotes == []:   # is this a regular, solo note (not part of a chord)?
               # yes, so sketch it
               x1 = msToXCoordinate(start)
               x2 = msToXCoordinate(start + length)
               y = midiPitchToYCoordinate(pitch)
               display.drawLine(x1=x1, y1=y, x2=x2, y2=y, color=partColor, thickness=2)

            else:   # note has a normal duration and it is part of a chord
               # first, add this note together with the other chord notes
               chordNotes.append([start, length, pitch])
               x1 = msToXCoordinate(start)
               x2 = msToXCoordinate(start + length)
               y = midiPitchToYCoordinate(pitch)

               # now, sketch all notes in the chord list using last note's length
               for start, ignoreThisLength, pitch, velocity, channel, panning, partColor in chordNotes:
                  # sketch this note using chord's length (provided by the last note in the chord)
                  display.drawLine(x1=x1, y1=y, x2=x2, y2=y, color=partColor, thickness=2)
               # now, all chord notes have been sketched

               # so, clear chord notes to continue handling new notes (if any)
               chordNotes = []

         # now, all notes have been sketched

      else:   # error check
         print(f'View.sketch(): Unrecognized type {type(material)}, expected Score, Part, or Phrase.')

   @staticmethod
   def notate(material, writeToFile=False):
      """Show the music as staff notation.

      Notation handles only a single phrase at a time (use Mod.consolidate() to combine a
      part's phrases first). It also lets you enter music as notation and save it.

      Args:
          material (Note, Phrase, Part, or Score): The music to show.
          writeToFile (bool, optional): Whether to also save the notation to a file.
      """
      # import internal notation renderer
      from PythonMusic.notationRenderer import _showNotation

      # wrap material into Score (following Write.midi pattern)
      if isinstance(material, Note):
         material = Phrase(material)
      if isinstance(material, Phrase):
         material = Part(material)
      if isinstance(material, Part):
         material = Score(material)

      if isinstance(material, Score):
         # get title from the score
         title = material.getTitle() if material.getTitle() else "Sheet Music"

         # delegate to internal renderer
         _showNotation(material, title, writeToFile)

      else:
         print("View.notate: material must be a Score, Part, Phrase, or Note.")

   notation = notate     # NOTE: some JythonMusic examples use View.notation()

   @staticmethod
   def internal(material):
      """Print the music's data to the screen.

      Args:
          material (Note, Phrase, Part, or Score): The music to print.
      """
      if type(material) in [Score, Part, Phrase]:   # material is valid
         # so print it
         print(material)

      else:   # otherwise, warn user of incorrect material type
         print("View.sketch: material must be a Score, Part, or Phrase.")


#######################################################################################
# Tests
#######################################################################################

if __name__ == "__main__":
   pass
