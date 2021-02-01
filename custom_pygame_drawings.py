# -*- coding: utf-8 -*-

# CUSTOM PYGAME DRAWING
# by Michal Wiraszka

# Contains a series of custom functions built on Pygame's basic drawing
# functionality. Tailored specifically for use in Würd Lürnür.

import pygame as pg
import pygame.gfxdraw as gfxdraw


def draw_circle(surface, x_position, y_position, radius, color):
    gfxdraw.aacircle(surface, x_position, y_position, radius, color)
    gfxdraw.filled_circle(surface, x_position, y_position, radius, color)

def dim_rect(surface, rect, color, alpha=64):
    # Draw a partially-transparent surface of given color onto area
    # defined by passed in rect object
    surface_to_dim = pg.Surface((rect.width, rect.height))
    surface_to_dim.set_alpha(alpha)
    surface_to_dim.fill(color)
    surface.blit(surface_to_dim, (rect.left, rect.top))


# Source (heavily modified): www.stackoverflow.com/questions/61523241/
def draw_rounded_rect(surface, rect, color, corner_radius):
    # Centres of circles defined for each corner of the rounded rectangle
    top_left = (rect.left+corner_radius, rect.top+corner_radius)
    top_right = (rect.right-corner_radius-1, rect.top+corner_radius)
    bottom_left = (rect.left+corner_radius, rect.bottom-corner_radius-1)
    bottom_right = (rect.right-corner_radius-1, rect.bottom-corner_radius-1)

    draw_circle(surface, *top_left, corner_radius, color)
    draw_circle(surface, *top_right, corner_radius, color)
    draw_circle(surface, *bottom_left, corner_radius, color)
    draw_circle(surface, *bottom_right, corner_radius, color)

    # Straight edges attach to curved corners using two separate (temp) rect
    # objects: one with the original height and one with the original width
    temp_rect = pg.Rect(rect)
    temp_rect.width -= 2*corner_radius
    temp_rect.center = rect.center
    pg.draw.rect(surface, color, temp_rect)

    temp_rect.width = rect.width
    temp_rect.height -= 2*corner_radius
    temp_rect.center = rect.center
    pg.draw.rect(surface, color, temp_rect)

def draw_bordered_rounded_rect(surface, rect, fill_color, border_color,
        corner_radius, border_thickness):
    if corner_radius < 0:
        raise ValueError('Corner radius must be greater than 0.')
    if border_thickness < 0:
        raise ValueError('Border radius must be greater than 0.')
    if (rect.width < 2*corner_radius) or (rect.height < 2*corner_radius):
        raise ValueError('Invalid box dimensions for given corner radius.')

    draw_rounded_rect(surface, rect, border_color, corner_radius)  # Exterior

    # Conflate outer_rect to get inner_rect dimensions; reduce each dimension
    # by TWICE the border thickness to account for borders on both sides of
    # the rect; compensate for default line thickness of 1
    inner_rect = rect.inflate(-2*border_thickness, -2*border_thickness)
    inner_radius = corner_radius - border_thickness + 1
    if inner_radius <= 0:
        pg.draw.rect(surface, fill_color, inner_rect)
    else:  # Interior edges
        draw_rounded_rect(surface, inner_rect, fill_color, inner_radius)


# Source (slightly modified): www.nerdparadise.com/programming/pygame/part5
def make_font(fonts, size):
    # get_fonts() returns a list of lowercase spaceless font names
    available = pg.font.get_fonts()
    choices = map(lambda x: x.lower().replace(' ', ''), fonts)
    for choice in choices:
        if choice in available:
            return pg.font.SysFont(choice, size)
    return pg.font.Font(None, size)

_cached_fonts = {}
def get_font(fonts, size):
    global _cached_fonts
    key = str(fonts) + '|' + str(size)
    font = _cached_fonts.get(key, None)
    if font is None:
        font = make_font(fonts, size)
        _cached_fonts[key] = font
    return font

_cached_text = {}
def get_text_surface(text, size, color, fonts):
    global _cached_text
    key = '|'.join(map(str, (fonts, size, color, text)))
    image = _cached_text.get(key, None)
    if image is None:
        font = get_font(fonts, size)
        image = font.render(text, True, color)
        _cached_text[key] = image
    return image
