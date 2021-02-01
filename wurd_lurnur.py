# -*- coding: utf-8 -*-

# WÜRD LÜRNÜR
# by Michal Wiraszka

# Please see accompanying README.md file for info.

# Some potentially ambiguous abbreviated names of variables used in code:
# x = x-position on screen;  y = y-position on screen; w = width;  h = height;
# char = character;  col = column;  cxt = context; def = definition;
# pos = part of speech;  prev = previous; pron = pronunciation;
# ssc = superscript; val = value

from datetime import datetime
from random import sample
import sys

import pandas as pd
import pygame as pg

from custom_pygame_drawings import (
    dim_rect,
    draw_bordered_rounded_rect,
    get_text_surface
)


BLACK = (10,10,10)
BROWN = (180,80,0)
DARK_BLUE = (13,24,61)
DARK_GREY = (70,70,70)
DARK_RED = (153,0,0)
GREEN = (0,153,40)
LIGHT_BLUE = (204,229,255)
LIGHT_GREY = (220,220,222)
MEDIUM_BLUE = (0,102,204)
MEDIUM_GREY = (160,160,160)
ORANGE = (240,120,51)
PURPLE = (130,30,255)
RED = (255,102,102)
WHITE = (250,250,250)
YELLOW = (196,185,24)

# Limit amount of characters in text to be displayed
MAX_CONTEXT_CHARS = 140
MAX_DEF_CHARS = 300
# First column in database containing session results
FIRST_SESSION_COL_INDEX = 8

TINY_FONT = 12
SMALL_FONT = 14
MEDIUM_FONT = 20
LARGE_FONT = 28
GIANT_FONT = 36
TITLE_FONT = 90
PREFERRED_FONTS = ['Arial', 'Verdana', 'Helvetica', 'Tahoma']

PARTS_OF_SPEECH = {
    'n.': {'full name': 'noun', 'color': ORANGE},
    'pron.': {'full name': 'pronoun', 'color': PURPLE},
    'prop. n.': {'full name': 'proper noun', 'color': RED},
    'idiom. n.': {'full name': 'idiomatic noun', 'color': MEDIUM_BLUE},
    'adj.': {'full name': 'adjective', 'color': YELLOW},
    'v.': {'full name': 'verb', 'color': GREEN},
    '': {'full name': 'unspecified', 'color': WHITE}
}

# All sound-related pygame loading and initializing
pg.mixer.pre_init(44100, -16, 2, 4096)
pg.mixer.init()

NEW_SESSION_SFX = pg.mixer.Sound('sound/new_session.ogg')
CARD_FLIP_SFX = pg.mixer.Sound('sound/card_flip.ogg')
TOGGLE_SFX = pg.mixer.Sound('sound/toggle.ogg')
APPEAR_SFX = pg.mixer.Sound('sound/appear.ogg')
LURNT_SFX = pg.mixer.Sound('sound/lurnt.ogg')
POP_SFX = pg.mixer.Sound('sound/popup.ogg')
QUIT_SFX = pg.mixer.Sound('sound/quit.ogg')
NEW_SESSION_SFX.set_volume(0.9)
CARD_FLIP_SFX.set_volume(0.2)
TOGGLE_SFX.set_volume(0.05)
APPEAR_SFX.set_volume(0.2)
LURNT_SFX.set_volume(0.1)
POP_SFX.set_volume(0.2)
QUIT_SFX.set_volume(0.2)

# All graphics-related pygame loading and initializing
pg.init()
WINDOW_W, WINDOW_H = (800,500)
WINDOW_RECT = pg.Rect(0, 0, WINDOW_W, WINDOW_H)
WINDOW = pg.display.set_mode((WINDOW_W, WINDOW_H), 0, 32)
pg.display.set_caption("Würd Lürnür v1.0")
CLOCK = pg.time.Clock()

BRICKS_BACKGROUND = pg.image.load('img/bricks_background.png').convert_alpha()
PRONOUNCE_ICON = pg.image.load('img/pronounce_icon.png').convert_alpha()
PASS_ICON = pg.image.load('img/pass_icon.png').convert_alpha()
FAIL_ICON = pg.image.load('img/fail_icon.png').convert_alpha()
ELLIPSIS_ICON = pg.image.load('img/ellipsis_icon.png').convert_alpha()
LEFT_ICON = pg.image.load('img/left_icon.png').convert_alpha()
RIGHT_ICON = pg.transform.rotate(LEFT_ICON, 180)
LURNT_ICON = pg.image.load('img/lurnt_icon.png').convert_alpha()

SMALL_ICON = ELLIPSIS_ICON.get_width()
LARGE_ICON = PASS_ICON.get_width()
ICON_SIZE_LURNT = LURNT_ICON.get_width()

WORD_IMG_SIZE = 150  # Image next to word definition
PAD = 4  # General padding constant; various multiples used to separate objects
SLIDER_WINDOW_MARGIN_Y = 20
SLIDER_W, SLIDER_H = (600,50)
SLIDER_Y = 270
SLIDER_TRACK_MARGIN_X, SLIDER_TRACK_MARGIN_Y = (10,22)
SLIDER_BUTTON_W, SLIDER_BUTTON_H = (10,40)
CARD_FRAME_MARGIN_X, CARD_FRAME_MARGIN_Y = (20,40)
STATS_FRAME_MARGIN_X, STATS_FRAME_MARGIN_Y = (250,100)
WORD_FRAME_H = 45
CONTEXT_FRAME_H = 90
POPUP_FRAME_H = 100
REGISTER_FRAME_W, REGISTER_FRAME_H = (250,75)
PREV_NEXT_BUTTON_W, PREV_NEXT_BUTTON_H = (75,75)


class Session:
    def __init__ (self, session_df, full_df):
        self.cards_df = session_df.copy()  # Copy df to prevent changes to orig.
        self.full_df = full_df.copy()
        # Isolate number portion of last stored Session name and add 1
        last_session_name = list(self.cards_df)[-1]
        last_index = int(last_session_name.split('#')[1].split(' -')[0])
        self.index = last_index + 1

        self.timestamp = get_timestamp_now()
        self.name = f'Session #{self.index} - {self.timestamp}'
        self.full_df[self.name] = ''  # Add empty column for new session

        self.current_card_index = 0
        self.showing_stats = False
        self.pronounce_icon_rect = None  # X-position altered by size of word

        # Initialize tallies which are shown when 'Show Stats' clicked
        self.db_total_card_count = len(full_df)
        self.card_count = len(self.cards_df.index)
        self.pass_count = 0
        self.fail_count = 0
        self.skip_count = 0
        self.lurnt_count = 0

        # Create list of Card objects containing every word added to Session
        self.cards = []
        for i in range(self.card_count):
            self.cards.append(Card(self.cards_df.iloc[i]))

        # Store all static Text and Rect objects in two dicts
        self.text, self.rects = get_all_static_surfaces()


    def show_stats(self):
        dim_rect(WINDOW, WINDOW_RECT, DARK_GREY, alpha=192)
        draw_box(WINDOW, self.rects['stats_frame'], LIGHT_BLUE, DARK_GREY)
        self.text['stats_header'].draw()
        self.text['ok_awesome'].draw(button=True)

        stats_text = [f'Total cards in database: {self.db_total_card_count}',
                      f'Cards this session: {self.card_count}',
                      f'Cards PASSED: {self.pass_count}',
                      f'Cards FAILED: {self.fail_count}',
                      f'Cards SKIPPED: {self.skip_count}',
                      f'Cards LÜRNT: {self.lurnt_count}']

        for i, stats_line in enumerate(stats_text):
            line_of_text = Text(stats_line, MEDIUM_FONT)
            # Centre first line of text and align start of other lines with it
            if i == 0:
                text_x = (self.rects['stats_frame'].left
                    + (self.rects['stats_frame'].width - line_of_text.w) // 2)
            line_of_text.x = text_x
            line_of_text.y = (self.rects['stats_frame'].top
                    + self.text['stats_header'].h + 3*PAD
                    + i*(line_of_text.h-2))  # Spacing between lines
            line_of_text.draw()

    def update_tallies(self, change_to):
        # Update the pass/fail/skip 'result' tallies; subtract from prev
        # result before adding to new result tally
        card = self.cards[self.current_card_index]
        change_from = card.result  # Result value prior to change
        if change_from == 'skip':
            self.skip_count -= 1
        elif change_from == 'pass':
            self.pass_count -= 1
            if card.lurnt:
                self.lurnt_count -= 1
        elif change_from == 'fail':
            self.fail_count -= 1

        if change_to == 'skip':
            self.skip_count += 1
        elif change_to == 'pass':
            self.pass_count += 1
            if card.passes_count == 4:
                self.lurnt_count += 1
        elif change_to == 'fail':
            self.fail_count += 1

    def change_card(self, direction):
        card = self.cards[self.current_card_index]
        if card.lurnt and not card.popup_played:
            card.lurnt_popup(self)
            card.popup_played = True
        else:
            CARD_FLIP_SFX.play()
        if card.result is None:
            # Manually flag this card as a 'skip'
            self.update_tallies('skip')
            card.update_result('skip', play_sfx=False)

        self.update_database()

        if direction == 'left':
            self.current_card_index -= 1
        elif direction == 'right':
            self.current_card_index += 1
        else:
            raise ValueError('Invalid direction for card change.')

    def update_database(self):
        # Updates internally-stored dataframe and overrides .csv file with it
        word = self.cards[self.current_card_index].word
        result = self.cards[self.current_card_index].result
        is_lurnt = self.cards[self.current_card_index].lurnt

        if is_lurnt:
            self.full_df.loc[self.full_df['Word']==word,['Lurnt']] = 'yes'
        else:
            self.full_df.loc[self.full_df['Word']==word,['Lurnt']] = ''

        if result == 'skip':
            result = '-'  # Mark any skipped words with a dash
        self.full_df.loc[self.full_df['Word']==word,[self.name]] = result
        self.full_df.to_csv('cards.csv', index=False, encoding='utf-8-sig')

        # Centre pop-up message on screen and hold for half a second but allow
        # User to exit with any key (except Q and W which exit the program)
        dim_rect(WINDOW, WINDOW_RECT, DARK_GREY, alpha=192)
        updating_text = Text("Updating database...", LARGE_FONT)
        popup_w = updating_text.w + 4*PAD  # Extra padding on sides
        popup_h = updating_text.h + 2*PAD
        popup_rect = pg.Rect((WINDOW_W-popup_w)//2, (WINDOW_H-popup_h)//2,
                             popup_w, popup_h)
        draw_box(WINDOW, popup_rect, LIGHT_BLUE, DARK_GREY)
        updating_text.x = popup_rect.left + 2*PAD
        updating_text.y = popup_rect.top + PAD
        updating_text.draw()

        pg.display.flip()
        current_time = pg.time.get_ticks()
        exit_time = current_time + 500

        while current_time < exit_time:
            current_time = pg.time.get_ticks()
            event = pg.event.get()
            for e in event:
                if ((e.type==pg.KEYDOWN and (e.key==pg.K_q or e.key==pg.K_w))
                        or (e.type == pg.QUIT)):
                    terminate_program()
                elif e.type == pg.KEYDOWN:
                    current_time = exit_time
            CLOCK.tick(5)

    def draw_card_screen(self, card):
        draw_box(WINDOW, self.rects['card_frame'], card.color, DARK_GREY)
        self.text['session_stats'].draw(button=True)
        self.text['quit'].draw(button=True)

        card.draw_word_frame(self)
        card.draw_context_frame(self)
        card.draw_defi_frame(self)
        card.draw_register_frame(self)
        card.draw_next_prev_buttons(self)
        if card.result_history:
            card.draw_result_history(self)


class Card:
    def __init__ (self, card_data):
        self.word = card_data.get('Word')
        self.word_variations = self.get_word_variations(card_data)

        self.pos_abbrev = card_data.get('Part of Speech').lower()
        self.pos_full_name = PARTS_OF_SPEECH[self.pos_abbrev]['full name']
        self.color = PARTS_OF_SPEECH[self.pos_abbrev]['color']

        # Truncate context and definition text to fit neatly on displayed card
        self.context = card_data.get('Context')
        if len(self.context) > MAX_CONTEXT_CHARS:
            self.context = self.context[:MAX_CONTEXT_CHARS-3] + ('...')
        self.definition = card_data.get('Definition')
        if len(self.definition) > MAX_DEF_CHARS:
            self.definition = self.definition[:MAX_DEF_CHARS-3] + ('...')

        past_sessions = card_data.iloc[FIRST_SESSION_COL_INDEX:]
        self.result_history = self.get_result_history(past_sessions)
        self.passes_count = self.count_passes(self.result_history)
        self.result = None

        self.lurnt = False  # Must be false since lurnt words were excluded
        self.popup_played = False  # To ensure victory pop-up only plays once
        self.show_context = True
        self.show_definition = False
        self.show_image = False
        self.img_path = f'./word_img/{self.word.lower()}.png'
        try:
            self.word_img = pg.image.load(self.img_path).convert_alpha()
        except Exception as e:
            print(f'{e.__class__.__name__}: image for {self.word}.')
            self.word_img = None


    def get_word_variations(self, card_data):
        # Spaced hyphen in word could indicate multiple spellings of word, so
        # store each part individually; add capitalized versions of words too
        if self.word.find(' - ') != -1:
            word_variations = self.word.split(' - ')
            words_to_cap = word_variations.copy()
            for word in words_to_cap:
                word_variations.append(self.word.capitalize())
        else:
            word_variations = [self.word, self.word.capitalize()]

        # Add word declensions to word variation list; sort by length as later
        # will need to prioritize longest variations when searching in text
        if type(card_data.get('Word Declensions')) == str:
            word_decl = card_data.get('Word Declensions').split(', ')
            word_decl_cap = [word.capitalize() for word in word_decl]
            word_variations.extend(word_decl)
            word_variations.extend(word_decl_cap)
            word_variations.sort(key=len, reverse=True)
        return word_variations

    def get_result_history(self, past_sessions):
        result_history = []
        for col_name, value in past_sessions.iteritems():
            if value in ('pass', 'fail'):
                # Last 16 characters of column names are always the timestamp
                # of when that session was created
                past_session = {'result': value, 'timestamp': col_name[-16:]}
                result_history.append(past_session)
        return result_history

    def count_passes(self, result_history):
        # Tally up all the passes from past sessions
        past_passes = 0
        for entry in self.result_history:
            if entry['result'] == 'pass':
                past_passes += 1
        return past_passes

    def pronounce(self):
        try:
            word_pronunciation = pg.mixer.Sound(f'word_pron/{self.word}.ogg')
            word_pronunciation.set_volume(0.8)
            word_pronunciation.play()
        except Exception as e:
            error_type = e.__class__.__name__
            print(f"{error_type}: pronunciation for '{self.word}'.")

    def toggle_result_selections(self):
        # Toggles across the 3 options left to right and returns new result
        if (self.result is None) or (self.result == 'skip'):
            return 'fail'
        if self.result == 'fail':
            return 'pass'
        if self.result == 'pass':
            return 'skip'

    def update_result(self, new_result, play_sfx=True):
        if play_sfx:
            TOGGLE_SFX.play()
        self.result = new_result
        if (self.result=='pass') and (self.passes_count==4):
            # After 5 passes total, flag card as 'lurnt'
            self.lurnt = True

    def draw_word_frame(self, session):
        # Centre objects horizontally in frame adding padding in between;
        # also centre vertically according to each object's individual height;
        # finally, store position of this card's pronunciation icon
        draw_box(WINDOW, session.rects['word_frame'])

        word_text = Text(self.word.replace(' - ', '/'), GIANT_FONT)
        pos_text = Text(f'({self.pos_abbrev})', LARGE_FONT)
        total_w = word_text.w + pos_text.w + LARGE_ICON + 2*PAD

        word_text.x = (WINDOW_W - total_w) // 2
        word_text.y = (session.rects['word_frame'].top
                       + ((WORD_FRAME_H-word_text.h) // 2))
        word_text.draw()

        pos_text.x = word_text.x + word_text.w + PAD
        pos_text.y = (session.rects['word_frame'].top
                      + ((WORD_FRAME_H-pos_text.h) // 2))
        pos_text.draw()

        icon_x = pos_text.x + pos_text.w + PAD
        icon_y = (session.rects['word_frame'].top
                  + (WORD_FRAME_H - LARGE_ICON) // 2)
        WINDOW.blit(PRONOUNCE_ICON, (icon_x, icon_y))
        session.pronounce_icon_rect = pg.Rect(
            icon_x, icon_y, LARGE_ICON, LARGE_ICON
        )

    def draw_result_history(self, session):
        if len(self.result_history) > 10:
            # If more than 10 pass/fail results stored, show only the last 10
            icon_count = 10
            entries = self.result_history[-10:]
            add_ellipsis = True
        else:
            icon_count = len(self.result_history)
            entries = self.result_history
            add_ellipsis = False

        # (Small) pass, fail & ellipsis icons all expected to be of same size;
        # spaces to add padding = number of icons + 1
        icons_rect_w = (icon_count * (SMALL_ICON+PAD)) + PAD
        if add_ellipsis:  # Make room for ellipsis icon if needed
            icons_rect_w += SMALL_ICON + PAD

        icons_rect_h = SMALL_ICON + 2*PAD
        icons_rect_x = WINDOW_W - CARD_FRAME_MARGIN_X - icons_rect_w
        icons_rect_y = CARD_FRAME_MARGIN_Y - PAD - icons_rect_h
        draw_box(WINDOW,
            pg.Rect((icons_rect_x, icons_rect_y, icons_rect_w, icons_rect_h)))

        # Draw icons in chronological sequence from left to right; store icon
        # surfaces in list for later mouse hovering collision handling
        icon_rects = []
        icon_x = icons_rect_x + PAD
        icon_y = icons_rect_y + PAD
        if add_ellipsis:
            WINDOW.blit(ELLIPSIS_ICON, (icon_x, icon_y))
            icon_x += SMALL_ICON + PAD
        for entry in entries:
            if entry['result']=='pass':
                icon = pg.transform.scale(
                    PASS_ICON, (SMALL_ICON, SMALL_ICON)
                )
            else:
                icon = pg.transform.scale(
                    FAIL_ICON, (SMALL_ICON, SMALL_ICON)
                )
            WINDOW.blit(icon, (icon_x, icon_y))
            icon_rects.append(
                pg.Rect(icon_x, icon_y, SMALL_ICON, SMALL_ICON)
            )
            icon_x += SMALL_ICON + PAD

        # Show that session's timestamp if mouse hovering over icon
        for i, rect in enumerate(icon_rects):
            if rect.collidepoint(pg.mouse.get_pos()):
                timestamp_text = Text(
                    self.result_history[i]['timestamp'], SMALL_FONT
                )
                mouse_x, mouse_y = pg.mouse.get_pos()
                # Limit x-position so that text doesn't go off screen
                x_limit = WINDOW_W - timestamp_text.w//2 - 2*PAD
                if mouse_x > x_limit:
                    mouse_x = x_limit
                timestamp_text.x = mouse_x - (timestamp_text.w//2)
                timestamp_text.y = mouse_y + 20  # Position 20px below mouse
                timestamp_text.draw(faded_background=True)

    def draw_context_frame(self, session):
        draw_box(WINDOW, session.rects['context_frame'])
        session.text['context_header'].draw()
        session.text['show_hide_cxt'].draw(button=True)

        if self.show_context:
            # Split, format, wrap, and draw text one line at a time: set x-pos
            # a bit past end of 'Definition' header with extra padding; split
            # symbol '|' in text separates multiple context examples
            text_x = session.rects['context_frame'].left + 2*PAD
            text_y = session.rects['context_frame'].top + 2*PAD
            max_width = session.rects['context_frame'].width - 4*PAD

            if '|' not in self.context:
                line_count = self.wrap_text(text=self.context,
                    font_size=MEDIUM_FONT, max_width=max_width,
                    position=(text_x,text_y), format='context')
            else:
                split_pt = self.context.find('|')
                line_count = self.wrap_text(
                    text=f'1. {self.context[:split_pt]}',
                    font_size=MEDIUM_FONT, max_width=max_width,
                    position=(text_x,text_y), format='context'
                )

                # Determine y-offset from first context example based on font
                # size, and force a new line for second example
                y_offset = line_count * (MEDIUM_FONT+3)
                _ = self.wrap_text(text=f'2. {self.context[split_pt+1:]}',
                    font_size=MEDIUM_FONT, max_width=max_width,
                    position=(text_x, text_y+y_offset), format='context')

    def draw_defi_frame(self, session):
        draw_box(WINDOW, session.rects['defi_frame'])
        draw_box(WINDOW, session.rects['img_frame'])
        session.text['definition_header'].draw()
        session.text['show_hide_def'].draw(button=True)

        if self.show_definition:
            text_x = session.rects['defi_frame'].left + 2*PAD
            text_y = session.rects['defi_frame'].top + 2*PAD
            max_width = session.rects['defi_frame'].width - 4*PAD

            _ = self.wrap_text(text=self.definition, font_size=MEDIUM_FONT,
                    max_width=max_width, position=(text_x,text_y),
                    format='definition')

        if self.word_img is not None and self.show_image:
            # Centre image inside square frame
            img_x = (session.rects['img_frame'].left + PAD
                     + ((WORD_IMG_SIZE-self.word_img.get_width()) // 2))
            img_y = (session.rects['img_frame'].top + PAD
                     + ((WORD_IMG_SIZE-self.word_img.get_height()) // 2))
            WINDOW.blit(self.word_img, (img_x, img_y))

    def draw_register_frame(self, session):
        draw_box(WINDOW, session.rects['register_frame'], fill_color=WHITE)
        session.text['register_header'].draw()

        # Change text color scheme and position of blue 'selection' rectangle
        if self.result == 'pass':
            header_colors = [BLACK, MEDIUM_GREY, MEDIUM_GREY]
            select_rect = session.rects['pass_button']
        elif (self.result == 'skip') or (self.result is None):
            header_colors = [MEDIUM_GREY, BLACK, MEDIUM_GREY]
            select_rect = session.rects['skip_button']
        elif self.result == 'fail':
            header_colors = [MEDIUM_GREY, MEDIUM_GREY, BLACK]
            select_rect = session.rects['fail_button']

        if self.result is not None:
            draw_box(WINDOW, select_rect, LIGHT_BLUE, MEDIUM_GREY)

        # Draw pass/skip/fail headers using color scheme based on selection
        pass_text = Text('PASS', SMALL_FONT, header_colors[0])
        pass_text.x = (session.rects['pass_button'].left +
                        (session.rects['pass_button'].width-pass_text.w) // 2)
        pass_text.y = session.rects['pass_button'].top
        pass_text.draw()

        skip_text = Text('SKIP', SMALL_FONT, header_colors[1])
        skip_text.x = (session.rects['skip_button'].left +
                        (session.rects['skip_button'].width-skip_text.w) // 2)
        skip_text.y = session.rects['skip_button'].top
        skip_text.draw()

        fail_text = Text('FAIL', SMALL_FONT, header_colors[2])
        fail_text.x = (session.rects['fail_button'].left +
                        (session.rects['fail_button'].width-fail_text.w) // 2)
        fail_text.y = session.rects['fail_button'].top
        fail_text.draw()

        # If pass or fail selected, add corresponding icon; the size of the
        # two icons are expected to be the same
        icon_y = pass_text.rect.bottom + PAD
        if self.result == 'pass':
            icon_x = (session.rects['pass_button'].left
                + (session.rects['pass_button'].width - LARGE_ICON) // 2)
            WINDOW.blit(PASS_ICON, (icon_x, icon_y))
        elif self.result == 'fail':
            icon_x = (session.rects['fail_button'].left
                + (session.rects['fail_button'].width - LARGE_ICON) // 2)
            WINDOW.blit(FAIL_ICON, (icon_x, icon_y))

    def draw_next_prev_buttons(self, session):
        # Build 'prev card'/'next card' buttons out of arrow icons & text
        left_icon_x = (session.rects['prev_button'].left
                       + (PREV_NEXT_BUTTON_W - LARGE_ICON) // 2)
        right_icon_x = (session.rects['next_button'].left
                       + (PREV_NEXT_BUTTON_W - LARGE_ICON) // 2)
        icon_y = session.rects['prev_button'].bottom - LARGE_ICON - PAD

        # Reuse 'card' Text object for both buttons by toggling x-position
        draw_box(WINDOW, session.rects['prev_button'], fill_color=WHITE)
        session.text['previous'].draw()
        session.text['card'].x = (session.rects['prev_button'].left +
            (session.rects['prev_button'].width-session.text['card'].w) // 2)
        session.text['card'].draw()
        WINDOW.blit(LEFT_ICON, (left_icon_x, icon_y))

        draw_box(WINDOW, session.rects['next_button'], fill_color=WHITE)
        session.text['next'].draw()
        session.text['card'].x = (session.rects['next_button'].left +
            (session.rects['next_button'].width-session.text['card'].w) // 2)
        session.text['card'].draw()
        WINDOW.blit(RIGHT_ICON, (right_icon_x, icon_y))

    def format_context(self, line_text, text_x, text_y, font_size,
                       line_count, surface=WINDOW):
        # Highlight any instances of the word (or its variations) in the
        # color corresponding to its part of speech
        x_offset = 0
        while len(line_text) > 0:
            cutoff_char = len(line_text)
            leftmost_word = None
            for word in self.word_variations:
                # Split text at the left-most occurence of the word; since
                # word variations ordered in decreasing order, longer words
                # searched first, ensuring full word gets captured; e.g.
                # 'demurred' caught before 'demur', so '-red' ending included
                word_index = line_text.find(word)
                if (word_index != -1) and (word_index < cutoff_char):
                    leftmost_word = word
                    cutoff_char = word_index

            if cutoff_char > 0:
                # Output all text up to cutoff char in regular font, as this
                # is either the whole line (default), or only up to beginning
                # of the word to be highlighted; manually remove auto-padding
                regular_text = Text(line_text[:cutoff_char], font_size)
                regular_text.x = text_x + x_offset
                regular_text.y = text_y + (line_count * (font_size+3))
                regular_text.draw()

                x_offset += regular_text.w - 2*PAD
                line_text = line_text[cutoff_char:]

            if leftmost_word is not None:
                # Output highlighted word and keep only text that follows it
                highlighted_word = Text(leftmost_word, font_size, self.color)
                highlighted_word.x = text_x + x_offset
                highlighted_word.y = text_y + (line_count * (font_size+3))
                highlighted_word.draw()

                x_offset += (highlighted_word.w - 2*PAD)
                line_text = line_text[len(leftmost_word):]

            elif line_text.startswith(' '):
                # If remaining text starts with an empty space, remove it
                line_text = line_text[1:]

    def format_definition(self, line_text, text_x, text_y, font_size,
                          line_count, surface=WINDOW):
        # Output any text within '[]' brackets in brown and superscript (ssc);
        # (expects string that begins with '[' and has a single ']')
        x_offset = 0
        close_bracket_index = line_text.find(']')
        ssc_text = Text(line_text[:close_bracket_index+1], font_size-5, BROWN)
        ssc_text.x = text_x + x_offset
        ssc_text.y = text_y + line_count*(font_size+3) - 3  # Shifted 3px up
        ssc_text.draw(surface=surface)

        x_offset += ssc_text.w
        remaining_text = Text(line_text[close_bracket_index+1:], font_size)
        remaining_text.x = text_x + x_offset
        remaining_text.y = text_y + line_count*(font_size+3)
        remaining_text.draw(surface=surface)

    def wrap_text(self, text, font_size, max_width, position,
                  color=DARK_BLUE, surface=WINDOW, format=None):
        # Assuming even distribution of wide and narrow chars, char limit
        # is calculated by reducing number of chars proportionally to width
        full_text = Text(text, font_size)
        char_limit_per_line = int(len(text) * max_width/full_text.w)
        line_count = 0
        text_x, text_y = position

        while len(text) > 0:
            line_chars = char_limit_per_line
            # If small-font superscript chars present, compensate width by
            # manually extending limit by 1 char for every 3 superscript chars
            if ((format == 'definition') and
                    (text[:line_chars].find('[') != -1) and
                    (text[:line_chars].find(']') != -1)):
                open_bracket_index = text[:line_chars].find('[')
                close_bracket_index = text[:line_chars].find(']')
                ssc_text = text[open_bracket_index : close_bracket_index+1]
                line_chars += (len(ssc_text) // 3)
            # If not last line, find word end by shifting to left one by one
            if len(text) > line_chars:
                while not text[:line_chars].endswith(' '):
                    line_chars -= 1
            else:
                line_chars = len(text)
            line_text = text[:line_chars]

            # Formatting specific to 'context' and 'definition' sections
            if format == 'context':
                self.format_context(
                    line_text, text_x, text_y, font_size, line_count
                )
            # Formatting specific to the 'definition' section
            elif format == 'definition':
                # Opening bracket '[' indicates the start of a 'domain' tag to
                # the word's definition, e.g. [in Law] or [archaic]; ensure
                # closing bracket exists on same line, and force a new line
                # for any domain tags found
                open_bracket_index = line_text.find('[')
                if open_bracket_index == 0:  # '[' is first char of line
                    close_bracket_index = line_text.find(']')
                    if close_bracket_index == -1:
                        text_to_output = Text(line_text, font_size)
                        text_to_output.x = text_x
                        text_to_output.y = text_y + line_count*(font_size+3)
                        text_to_output.draw(surface=surface)
                    else:
                        # There could be multiple '[]' sets on single line;
                        # ensure that only single tag is sent to formatting
                        next_bracket_index = line_text[1:].find('[')
                        if next_bracket_index != -1:
                            # Compensate for [1:] char skip
                            next_bracket_index += 1
                            line_text = line_text[:next_bracket_index]
                            line_chars = len(line_text)
                        self.format_definition(
                            line_text, text_x, text_y, font_size, line_count
                        )
                else:
                    # Either no open bracket exists or there is text before
                    # it, so next output will be non-superscript text
                    if open_bracket_index > 0:
                        # Open bracket exists but there is text before it so
                        # force that text to be output first by truncating
                        # line text to just this pre-bracket text
                        line_text = line_text[:open_bracket_index]
                        line_chars = len(line_text[:open_bracket_index])
                    normal_text = Text(line_text, font_size)
                    normal_text.x = text_x
                    normal_text.y = text_y + line_count*(font_size+3)
                    normal_text.draw(surface=surface)
            # Output full line (basic text wrapping - no formatting)
            else:
                full_line_text = Text(line_text, font_size)
                full_line_text.x = text_x
                full_line_text.y = text_y + line_count*(font_size+3)
                full_line_text.draw(surface=surface)

            text = text[line_chars:]
            line_count += 1
        return line_count

    def lurnt_popup(self, session):
        LURNT_SFX.play()
        # Fade background with semi-transparent surface; find widest of the
        # two lines of text and base pop-up window width on that
        dim_rect(WINDOW, WINDOW_RECT, DARK_GREY, alpha=192)
        line_1_text = Text("Congrats! You've lürnt", LARGE_FONT)
        lurnt_word_text = Text(self.word, GIANT_FONT, BLACK)
        line_2_total_w = lurnt_word_text.w + 3*PAD + ICON_SIZE_LURNT
        popup_frame_w = max(line_1_text.w,line_2_total_w) + 6*PAD

        popup_frame_rect = pg.Rect(
            (WINDOW_W-popup_frame_w) // 2, (WINDOW_H-POPUP_FRAME_H) // 2,
            popup_frame_w, POPUP_FRAME_H
        )
        draw_box(WINDOW, popup_frame_rect, LIGHT_BLUE, DARK_GREY)

        # Draw objects onto pop-up
        line_1_text.x = (popup_frame_rect.left
                         + (popup_frame_rect.width - line_1_text.w) // 2)
        line_1_text.y = popup_frame_rect.top + PAD
        line_1_text.draw()

        lurnt_icon_x = (popup_frame_rect.left
                         + (popup_frame_rect.width - line_2_total_w) // 2)
        lurnt_icon_y = line_1_text.rect.bottom + PAD
        WINDOW.blit(LURNT_ICON, (lurnt_icon_x, lurnt_icon_y))

        lurnt_word_text.x = lurnt_icon_x + ICON_SIZE_LURNT + 3*PAD
        lurnt_word_text.y = lurnt_icon_y - PAD
        lurnt_word_text.draw()

        # Display pop-up for two seconds before it disappears
        pg.display.flip()
        current_time = pg.time.get_ticks()
        exit_time = current_time + 2000

        while current_time < exit_time:
            current_time = pg.time.get_ticks()
            event = pg.event.get()
            for e in event:
                # Allow User to terminate program with Q or W when pop-up is
                # displaying; any other key will exit pop-up instantly
                if ((e.type==pg.KEYDOWN and (e.key==pg.K_q or e.key==pg.K_w))
                        or (e.type == pg.QUIT)):
                    session.update_database()
                    terminate_program()
                elif e.type == pg.KEYDOWN:
                    current_time = exit_time
            CLOCK.tick(5)


class Slider:
    # Adapted from:
    # www.dreamincode.net/forums/topic/401541-buttons-and-sliders-in-pygame/
    def __init__(self, val, max_val, min_val):
        self.val = val  # Slider's moveable 'button' value
        self.max_val = max_val  # Maximum value at far right
        self.min_val = min_val  # Minimum value at far left
        self.range = self.max_val - self.min_val
        self.hit = False  # Flag when slider's button is clicked ('hit')

        # Slider's position on screen and dimensions
        self.x, self.y = ((WINDOW_W-SLIDER_W)//2, SLIDER_Y)
        self.w, self.h = (SLIDER_W, SLIDER_H)

        # Static graphics - slider bg (+10px pad on sides) & all static text
        self.surface = pg.surface.Surface((self.w, self.h))
        self.surface.fill(DARK_BLUE)
        pg.draw.rect(self.surface, MEDIUM_GREY, (0, 0, self.w, self.h), 3)

        slider_track_h = (SLIDER_H - 2*SLIDER_TRACK_MARGIN_Y)
        pg.draw.rect(self.surface, LIGHT_GREY,
            (SLIDER_TRACK_MARGIN_X, SLIDER_TRACK_MARGIN_Y,
             self.w - 2*SLIDER_TRACK_MARGIN_X, slider_track_h), 0)

        self.welcome_text = Text('Welcome to', MEDIUM_FONT, BLACK)
        # Override default preferred fonts with this set:
        title_fonts = ['Chalkduster', 'Yellowtail', 'Didot', 'Helvetica']
        self.wurd_lurnur_text = Text(
            'Würd Lürnür', TITLE_FONT, BLACK, fonts=title_fonts
        )
        self.how_many_text = Text(
            'How many würds would you like to lürn?', MEDIUM_FONT, BLACK
        )
        self.start_text = Text('Start', GIANT_FONT)

        self.wurd_lurnur_text.x = (WINDOW_W - self.wurd_lurnur_text.w) // 2
        self.welcome_text.x = self.wurd_lurnur_text.x  # Align left sides
        self.how_many_text.x = (WINDOW_W - self.how_many_text.w) // 2
        self.welcome_text.y = SLIDER_WINDOW_MARGIN_Y
        self.wurd_lurnur_text.y = (self.welcome_text.y +
                                    self.welcome_text.h + PAD)
        self.how_many_text.y = self.y - (self.how_many_text.h + PAD)
        self.start_text.x = (WINDOW_W - self.start_text.w) // 2
        self.start_text.y = WINDOW_H-SLIDER_WINDOW_MARGIN_Y-self.start_text.h

        # Dynamic graphics - orange button surface & slider value underneath
        self.button_surface = pg.surface.Surface(
            (SLIDER_BUTTON_W, SLIDER_BUTTON_H)
        )
        pg.draw.rect(self.button_surface, BROWN,
            (0, 0, SLIDER_BUTTON_W, SLIDER_BUTTON_H))
        pg.draw.rect(self.button_surface, DARK_RED,
            (2, 2, SLIDER_BUTTON_W-4, SLIDER_BUTTON_H-4))

        relative_x = (self.val - self.min_val) / self.range
        self.button_x = (int(relative_x * (self.w-2*SLIDER_BUTTON_W))
                         + SLIDER_BUTTON_W)
        self.button_rect = self.button_surface.get_rect(
                                center=(self.button_x, self.h//2))

        self.val_text = Text(str(int(self.val)), LARGE_FONT, DARK_BLUE)
        self.val_text.x = self.button_x - (self.val_text.w // 2)
        self.val_text.y = self.y + self.h + PAD


    def draw(self):
        surface = self.surface.copy()  # Static bg (slider's track) copied
        relative_x = (self.val - self.min_val) / self.range
        self.button_x = (int(relative_x * (self.w-2*SLIDER_BUTTON_W))
                         + SLIDER_BUTTON_W)
        self.button_rect = self.button_surface.get_rect(
                                center=(self.button_x, self.h//2))
        surface.blit(self.button_surface, self.button_rect)
        self.button_rect.move_ip(self.x, self.y)
        WINDOW.blit(surface, (self.x, self.y))

        # Update x-position and text based on slider
        self.val_text.text = str(int(self.val))
        self.val_text.x = self.x + self.button_x - (self.val_text.w // 2)
        self.val_text.draw(faded_background=True)

    def move(self, auto_move_amount=None):
        old_val = self.val
        if not auto_move_amount:
            x_offset = pg.mouse.get_pos()[0] - self.x + SLIDER_BUTTON_W//2
            self.val = (x_offset/self.w * self.range) + self.min_val
        else:
            # Slider incremented by 1 using left/right keys
            self.val = self.val + auto_move_amount
        # Limit slider movement up to the far ends
        if self.val < self.min_val:
            self.val = self.min_val
        elif self.val > self.max_val:
            self.val = self.max_val


class Text:
    # Create text surface with default color of dark blue
    def __init__(self, new_text, font_size, font_color=DARK_BLUE,
                 fonts=PREFERRED_FONTS):
        self.font_size = font_size
        self.font_color = font_color
        self.fonts = fonts
        self.text = new_text
        self.surface = get_text_surface(
            self.text, self.font_size, self.font_color, self.fonts
        )
        self.w = self.surface.get_width() + 2*PAD
        self.h = self.surface.get_height() + 2*PAD
        self.x, self.y = None, None

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        self._text = text
        self.surface = get_text_surface(
            self._text, self.font_size, self.font_color, self.fonts
        )
        self.w = self.surface.get_width() + 2*PAD
        self.h = self.surface.get_height() + 2*PAD

    @property
    def rect(self):  # Dynamically update rect based on x and y position
        if (self.x is not None) and (self.y is not None):
            return pg.Rect(self.x, self.y, self.w, self.h)
        else:
            return None

    def draw(self, button=False, faded_background=False, surface=WINDOW):
        if self.rect is not None:
            if button:
                draw_box(surface, self.rect, fill_color=WHITE)
            elif faded_background:
                # Create blurry 'faded' bg effect with 5 different-sized rects
                for i in range(4):
                    bg_layer = self.rect.inflate(
                        -PAD + (PAD//2)*i, -PAD + (PAD//2)*i
                    )
                    dim_rect(surface, bg_layer, LIGHT_GREY)
            # Shift text position to compensate for button padding
            surface.blit(self.surface, (self.x + PAD, self.y + PAD))
        else:
            print("Must first define text's position on screen!")


def get_all_static_surfaces():
    # Create all Text objects and store them in a dict; buttons in BLACK
    text = {
        'session_stats': Text('Session Stats', SMALL_FONT, BLACK),
        'quit': Text('Quit', SMALL_FONT, BLACK),
        'stats_header': Text('Session Stats', LARGE_FONT),
        'ok_awesome': Text('Ok, awesome!', MEDIUM_FONT, BLACK),
        'context_header': Text('Context', MEDIUM_FONT),
        'definition_header': Text('Definition', MEDIUM_FONT),
        'show_hide_cxt': Text('Show/Hide', SMALL_FONT, BLACK),
        'show_hide_def': Text('Show/Hide', SMALL_FONT, BLACK),
        'previous': Text('Previous', SMALL_FONT, BLACK),
        'next': Text('Next', SMALL_FONT, BLACK),
        'card': Text('card', SMALL_FONT, BLACK),
        'register_header': Text('Register card result:', MEDIUM_FONT, BLACK)
    }

    # Append Rect objects (x,y,w,h) individually using constants and
    # attributes of previously appended Rects
    rects = {}
    rects['card_frame'] = pg.Rect(
        CARD_FRAME_MARGIN_X,
        CARD_FRAME_MARGIN_Y,
        WINDOW_W - 2*CARD_FRAME_MARGIN_X,
        WINDOW_H - 2*CARD_FRAME_MARGIN_Y
    )
    rects['stats_frame'] = pg.Rect(
        STATS_FRAME_MARGIN_X,
        STATS_FRAME_MARGIN_Y,
        WINDOW_W - 2*STATS_FRAME_MARGIN_X,
        WINDOW_H - 2*STATS_FRAME_MARGIN_Y
    )
    rects['word_frame'] = pg.Rect(
        rects['card_frame'].left + 2*PAD,
        rects['card_frame'].top + 2*PAD,
        rects['card_frame'].width - 4*PAD,
        WORD_FRAME_H
    )

    # Align left-side headers with start of word frame before continuing
    # with rects since some rect positions will be based on this
    text['context_header'].x = rects['word_frame'].left + PAD
    text['show_hide_cxt'].x = text['context_header'].x
    text['definition_header'].x = text['context_header'].x
    text['show_hide_def'].x = text['context_header'].x

    text['context_header'].y = rects['word_frame'].bottom + 2*PAD
    text['show_hide_cxt'].y = text['context_header'].rect.bottom
    text['definition_header'].y = (text['context_header'].y
                                   + CONTEXT_FRAME_H + 2*PAD)
    text['show_hide_def'].y = text['definition_header'].rect.bottom

    rects['context_frame'] = pg.Rect(
        text['definition_header'].rect.right + 2*PAD,
        text['context_header'].y - PAD,
        (rects['word_frame'].width
            - text['definition_header'].rect.width - 3*PAD),
        CONTEXT_FRAME_H
    )
    rects['img_frame'] = pg.Rect(
        rects['card_frame'].right - WORD_IMG_SIZE - 4*PAD,
        rects['context_frame'].bottom + PAD,
        WORD_IMG_SIZE + 2*PAD,
        WORD_IMG_SIZE + 2*PAD
    )
    rects['defi_frame'] = pg.Rect(
        rects['context_frame'].left,
        rects['context_frame'].bottom + PAD,
        rects['context_frame'].width - rects['img_frame'].width - PAD,
        rects['img_frame'].height
    )

    rects['register_frame'] = pg.Rect(
        (WINDOW_W - REGISTER_FRAME_W) // 2,
        rects['card_frame'].bottom - 2*PAD - REGISTER_FRAME_H,
        REGISTER_FRAME_W,
        REGISTER_FRAME_H
    )
    rects['prev_button'] = pg.Rect(
        rects['register_frame'].left - PREV_NEXT_BUTTON_W - PAD,
        rects['register_frame'].top,
        PREV_NEXT_BUTTON_W,
        PREV_NEXT_BUTTON_H,
    )
    rects['next_button'] = pg.Rect(
        rects['register_frame'].right + PAD,
        rects['register_frame'].top,
        PREV_NEXT_BUTTON_W,
        PREV_NEXT_BUTTON_H,
    )

    # Evenly space out 3 buttons inside register frame
    rects['pass_button'] = pg.Rect(
        rects['register_frame'].left + PAD,
        rects['register_frame'].top + PAD,
        (rects['register_frame'].width - 4*PAD) // 3,
        rects['register_frame'].height - 2*PAD
    )
    rects['skip_button'] = pg.Rect(
        rects['pass_button'].right + PAD,
        rects['pass_button'].top,
        rects['pass_button'].width,
        rects['pass_button'].height
    )
    rects['fail_button'] = pg.Rect(
        rects['skip_button'].right + PAD,
        rects['skip_button'].top,
        rects['skip_button'].width,
        rects['skip_button'].height
    )

    # Define positions of remaining Text objects based on all this
    text['previous'].x = (rects['prev_button'].left
        + (rects['prev_button'].width - text['previous'].w) // 2)
    text['previous'].y = rects['prev_button'].top + PAD
    # Bring 'card' word up closer to 'next' by manually removing padding;
    # x-position defined in draw function in order to re-use Text object
    text['card'].y = text['previous'].y + text['previous'].h - 2*PAD
    text['next'].x = (rects['next_button'].left
            + (rects['next_button'].width - text['next'].w) // 2)
    text['next'].y = rects['next_button'].top + PAD

    text['session_stats'].x = CARD_FRAME_MARGIN_X
    text['session_stats'].y = (CARD_FRAME_MARGIN_Y
            - (text['session_stats'].h + PAD))
    text['quit'].x = text['session_stats'].rect.right + PAD
    text['quit'].y = text['session_stats'].y

    text['stats_header'].x = (rects['stats_frame'].left
            + (rects['stats_frame'].width - text['stats_header'].w) // 2)
    text['stats_header'].y = rects['stats_frame'].top + PAD
    text['ok_awesome'].x = (rects['stats_frame'].left
            + (rects['stats_frame'].width - text['ok_awesome'].w) // 2)
    text['ok_awesome'].y = (rects['stats_frame'].bottom
            - text['ok_awesome'].h - 2*PAD)

    text['register_header'].x = (rects['register_frame'].left
        + (rects['register_frame'].width-text['register_header'].w) // 2)
    text['register_header'].y = (rects['register_frame'].top
                                    - text['register_header'].h)
    return text, rects


def draw_box(surface, rect, fill_color=LIGHT_GREY, border_color=MEDIUM_GREY,
        corner_radius=5, border_thickness=2):
    # Wrapper function to set default values for local imported function
    draw_bordered_rounded_rect(surface, rect, fill_color, border_color,
        corner_radius, border_thickness)

def get_timestamp_now():
    # Get current time and return as a neatly formatted string
    time_now = datetime.now()
    _day = time_now.strftime('%d')
    _month = time_now.strftime('%m')
    _year = time_now.strftime('%Y')
    _hour = time_now.strftime('%H')
    _minute = time_now.strftime('%M')
    return f'{_day}.{_month}.{_year} {_hour}:{_minute}'

def terminate_program():
    QUIT_SFX.play()
    pg.time.delay(300)  # 0.3s delay to allow SFX to finish playing
    pg.quit()
    sys.exit()

def init_slider(start_val, max_val, min_val, unlurnt_card_count):
    # Translate 'max' string inputs to integer values; slider start value can
    # be at most the upper limit value of the slider
    if max_val == 'max':
        max_val = unlurnt_card_count
    if start_val == 'max':
        start_val = max_val

    slider_criteria = (
        (isinstance(max_val, int)),
        (isinstance(min_val, int)),
        (isinstance(start_val, int)),
        (max_val > min_val),
        (min_val > 0),
        (min_val <= unlurnt_card_count),
        (max_val <= unlurnt_card_count),
        (start_val <= unlurnt_card_count)
    )
    if all(slider_criteria):
        slider = Slider(start_val, max_val, min_val)
    else:
        print('Unable to instantiate slider.')
        terminate_program()
    return slider


def main():
    # Output welcome message to shell; transfer database of cards into df
    print('\n'*25 + '*'*68 + '\n' + ' '*28 + 'Würd Lürnür' + '\n' + '*'*68)
    with open('cards.csv', 'r') as f:
        full_df = pd.read_csv(f)

    # Get indices for all the 'unlurnt' words in the dataframe
    unlurnt_indices = [i for i, row in full_df.iterrows()
                       if row['Lurnt'] != 'yes']
    if len(unlurnt_indices) == 0:
        print('Congratulations! All words in database are lürnt.')
        terminate_program()

    slider = init_slider(start_val='max', max_val='max', min_val=1,
                         unlurnt_card_count=(len(unlurnt_indices)))
    on_slider_screen = True
    start_session = False
    new_session_init = False

    # MAIN GAME LOOP
    while True:
        WINDOW.blit(BRICKS_BACKGROUND, (0,0))
        if start_session:
            on_slider_screen = False
        if on_slider_screen:
            slider.welcome_text.draw(faded_background=True)
            slider.wurd_lurnur_text.draw(faded_background=True)
            slider.how_many_text.draw(faded_background=True)
            slider.start_text.draw(button=True)
            if slider.hit:
                slider.move()
            slider.draw()
        else:
            if not new_session_init:
                # Determine which cards (dataframe indices) session will
                # comprise of and how to order them; option to pass additional
                # attribute in to module upon execution:
                # 1) rand - shuffle cards using random.sample (default)
                # 2) chron - order chronologically, i.e. by date added
                # 3) alpha - order alphabetically
                order_cards = sys.argv[1] if len(sys.argv)-1 == 1 else 'rand'
                if order_cards == 'rand':
                    session_indices = sample(unlurnt_indices, int(slider.val))
                    df = full_df.iloc[session_indices]
                elif order_cards == 'chron':
                    session_indices = unlurnt_indices[:int(slider.val)]
                    df = full_df.iloc[session_indices]
                else:  # alpha: isolate all unlurnt rows before alphabetizing
                    df = full_df.iloc[unlurnt_indices]
                    df = df.loc[df['Word'].str.lower().sort_values().index]
                    df = df.iloc[:int(slider.val)]
                session = Session(df, full_df)
                NEW_SESSION_SFX.play()
                new_session_init = True

            card = session.cards[session.current_card_index]
            session.draw_card_screen(card)

            if session.showing_stats:
                session.show_stats()

        event = pg.event.get()
        for e in event:
            if e.type == pg.QUIT:
                if not on_slider_screen:
                    session.update_database()
                terminate_program()
            # MOUSE EVENTS
            if (e.type == pg.MOUSEBUTTONDOWN) and on_slider_screen:
                # On slider screen, User interacts with slider or start button
                if slider.start_text.rect.collidepoint(e.pos):
                    start_session = True
                elif (slider.button_rect.collidepoint(e.pos) or
                        slider.val_text.rect.collidepoint(e.pos)):
                    slider.hit = True

            elif (e.type == pg.MOUSEBUTTONDOWN) and session.showing_stats:
                if (session.text['ok_awesome'].rect.collidepoint(e.pos) or
                        not session.rects['stats_frame'].collidepoint(e.pos)):
                    # On card screen when showing stats, User can exit stats
                    # by clicking 'awesome' button or outside of stats frame
                    session.showing_stats = False
                    POP_SFX.play()

            elif (e.type == pg.MOUSEBUTTONDOWN) and not session.showing_stats:
                # On card screen when not showing stats, many things clickable
                # 1) Result buttons: only update result if it has changed
                if (session.rects['pass_button'].collidepoint(e.pos) and
                        (card.result != 'pass')):
                    session.update_tallies('pass')
                    card.update_result('pass')
                elif (session.rects['skip_button'].collidepoint(e.pos) and
                        (card.result != 'skip')):
                    session.update_tallies('skip')
                    card.update_result('skip')
                elif (session.rects['fail_button'].collidepoint(e.pos) and
                        (card.result != 'fail')):
                    session.update_tallies('fail')
                    card.update_result('fail')

                # 2) prev/Next buttons: first check if any cards left
                elif (session.rects['prev_button'].collidepoint(e.pos) and
                        (session.current_card_index > 0)):
                    session.change_card('left')
                elif (session.rects['next_button'].collidepoint(e.pos) and
                        session.current_card_index < (session.card_count-1)):
                    session.change_card('right')

                # 3) Toggle showing context and definition, either by clicking
                # buttons under headers, or the frames beside; image can be
                # toggled separately, but only by clicking on it
                elif (
                        session.rects['context_frame'].collidepoint(e.pos) or
                        session.text['show_hide_cxt'].rect.collidepoint(e.pos)
                    ):
                    card.show_context = not card.show_context
                    APPEAR_SFX.play()
                elif session.rects['defi_frame'].collidepoint(e.pos):
                    card.show_definition = not card.show_definition
                    APPEAR_SFX.play()
                elif session.text['show_hide_def'].rect.collidepoint(e.pos):
                    card.show_definition = not card.show_definition
                    card.show_image = card.show_definition
                    APPEAR_SFX.play()
                elif session.rects['img_frame'].collidepoint(e.pos):
                    card.show_image = not card.show_image
                    APPEAR_SFX.play()

                # 4) Pronounce icon: play pronunciation track for that word
                elif session.pronounce_icon_rect.collidepoint(e.pos):
                    card.pronounce()

                # 5) Session Stats and Quit buttons
                elif session.text['session_stats'].rect.collidepoint(e.pos):
                    session.showing_stats = True
                    POP_SFX.play()
                elif session.text['quit'].rect.collidepoint(e.pos):
                    session.update_database()
                    terminate_program()

            # Mouse button released - deactivate slider button
            elif (e.type == pg.MOUSEBUTTONUP) and on_slider_screen:
                slider.hit = False

            # KEYBOARD EVENTS
            if e.type == pg.KEYDOWN:
                if (e.key == pg.K_q) or (e.key == pg.K_w):
                    if not on_slider_screen:
                        session.update_database()
                    terminate_program()
                # Keyboard controls ...while on slider screen
                if on_slider_screen:
                    if e.key == pg.K_LEFT:
                        slider.move(-1)
                        TOGGLE_SFX.play()
                    if e.key == pg.K_RIGHT:
                        slider.move(1)
                        TOGGLE_SFX.play()
                    if e.key == pg.K_RETURN:
                        on_slider_screen = False
                # ...while on card screen & stats not clicked
                elif not on_slider_screen and not session.showing_stats:
                    if e.key == pg.K_SPACE:
                        new_result = card.toggle_result_selections()
                        session.update_tallies(new_result)
                        card.update_result(new_result)
                    if e.key == pg.K_c:
                        card.show_context = not card.show_context
                        APPEAR_SFX.play()
                    if e.key == pg.K_d:
                        card.show_definition = not card.show_definition
                        card.show_image = card.show_definition
                        APPEAR_SFX.play()
                    if e.key == pg.K_p:
                        card.pronounce()
                    if e.key == pg.K_s:
                        session.showing_stats = True
                        POP_SFX.play()
                    if e.key == pg.K_LEFT:
                        if session.current_card_index > 0:
                            session.change_card('left')
                    if (e.key == pg.K_RIGHT) or (e.key == pg.K_RETURN):
                        if session.current_card_index < session.card_count-1:
                            session.change_card('right')
                # ...while on card screen & stats clicked; User can exit
                # stats with any key apart from W and Q (checked earlier)
                elif not on_slider_screen and session.showing_stats:
                    session.showing_stats = False
                    POP_SFX.play()
        pg.display.update()
        CLOCK.tick(60)  # Update screen at a constant 60 FPS

if __name__ == "__main__":
    main()
