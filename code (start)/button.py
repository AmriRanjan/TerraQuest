import pygame

class Button():
    def __init__(self, image, pos, text_input, font, base_color, hovering_color, outline_color, outline_thickness, rotates = False):
        self.image = image  # surface of button
        self.x_pos = pos[0]
        self.y_pos = pos[1]
        self.text_input = text_input
        self.font = font
        self.base_color = base_color
        self.hovering_color = hovering_color
        self.outline_color = outline_color
        self.outline_thickness = outline_thickness
        self.original_image = image  # store original image for rotation
        self.angle = 0  # initial angle for rotation
        self.rotates = rotates
        
        if self.text_input is not None and self.font is not None:
            self.text = self.font.render(self.text_input, True, self.base_color)
        else:
            self.text = None  # for icon-only buttons (no text) then text of button is none and not rendered

        if self.image is None: # if no image provided, then button image can be taken as its text
            self.image = self.text
        self.rect = self.image.get_rect(center=(self.x_pos, self.y_pos))

        if self.text is not None:
            self.text_rect = self.text.get_rect(center=(self.x_pos, self.y_pos)) 
            # this ensures that if text present, it's rectangle is at centre of the button, 
			# independent of the image size. Then when we blit it, we can use rectangle's 
			# position to place it at exactly centre of button
        else:
            self.text_rect = None

    def update(self, screen):
        screen.blit(self.image, self.rect) # blit button image or if no image then self.image is the text that is blitted

        # creates outline of text above button image (if present), or else outline made above display surface
        if self.text is not None:
            # Loop through small x-offsets around the text position
            for dx in range(-self.outline_thickness, self.outline_thickness + 1):
                # Loop through small y-offsets around the text position
                for dy in range(-self.outline_thickness, self.outline_thickness + 1):
                    if dx != 0 or dy != 0:  # avoid overwriting center
                        # move outline text rectangle by offset and blit it for outline effect
                        outline_rect = self.text_rect.move(dx, dy)
                        outline_text = self.font.render(self.text_input, True, self.outline_color)
                        screen.blit(outline_text, outline_rect)
            screen.blit(self.text, self.text_rect) # blit text on top of outline

    def checkForInput(self, position):
        if self.rect.collidepoint(position):
            return True
        return False

    def hover(self, position):
        if self.text is not None:
            if self.rect.collidepoint(position):
                self.text = self.font.render(self.text_input, True, self.hovering_color)
            else:
                self.text = self.font.render(self.text_input, True, self.base_color)
        elif self.rotates:
            if self.rect.collidepoint(position):
                self.angle = (self.angle-2) % 360 # rotate by -2 degrees on hover in the while true loop
            
            self.image = pygame.transform.rotate(self.original_image, self.angle) # perform rotation operation on image
            self.rect = self.image.get_rect(center=(self.x_pos, self.y_pos)) # recentre rectangle after rotation