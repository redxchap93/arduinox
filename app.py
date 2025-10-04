#!/usr/bin/env python3
"""
Snake Game Implementation using Pygame
"""

import pygame
import sys
import logging
import random
from typing import Tuple, List, Optional
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Direction(Enum):
    """Enumeration for snake directions"""
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class Snake:
    """Snake class representing the player's snake"""
    
    def __init__(self, start_position: Tuple[int, int]):
        self.body = [start_position]
        self.direction = Direction.RIGHT
        self.grow_pending = False
        
    def move(self) -> None:
        """Move the snake one step in its current direction"""
        head_x, head_y = self.body[0]
        dx, dy = self.direction.value
        new_head = (head_x + dx, head_y + dy)
        self.body.insert(0, new_head)
        
        if not self.grow_pending:
            self.body.pop()
        else:
            self.grow_pending = False
            
    def change_direction(self, new_direction: Direction) -> None:
        """Change the direction of the snake, preventing 180-degree turns"""
        # Prevent 180-degree turns
        if (new_direction.value[0] * -1, new_direction.value[1] * -1) != self.direction.value:
            self.direction = new_direction
            
    def grow(self) -> None:
        """Increase the snake's length"""
        self.grow_pending = True
        
    def get_head(self) -> Tuple[int, int]:
        """Get the position of the snake's head"""
        return self.body[0]
        
    def collides_with_self(self) -> bool:
        """Check if the snake collides with itself"""
        head = self.get_head()
        return head in self.body[1:]

class Food:
    """Food class representing the food that the snake eats"""
    
    def __init__(self, grid_size: Tuple[int, int], snake_body: List[Tuple[int, int]]):
        self.grid_size = grid_size
        self.position = self.generate_position(snake_body)
        
    def generate_position(self, snake_body: List[Tuple[int, int]]) -> Tuple[int, int]:
        """Generate a random position for food that doesn't overlap with the snake"""
        while True:
            x = random.randint(0, self.grid_size[0] - 1)
            y = random.randint(0, self.grid_size[1] - 1)
            if (x, y) not in snake_body:
                return (x, y)
                
    def respawn(self, snake_body: List[Tuple[int, int]]) -> None:
        """Respawn food at a new location"""
        self.position = self.generate_position(snake_body)

class Game:
    """Main game class that manages game state and logic"""
    
    def __init__(self, width: int = 800, height: int = 600, cell_size: int = 20):
        try:
            pygame.init()
            self.width = width
            self.height = height
            self.cell_size = cell_size
            self.grid_width = width // cell_size
            self.grid_height = height // cell_size
            
            # Create the game window
            self.screen = pygame.display.set_mode((width, height))
            pygame.display.set_caption("Snake Game")
            self.clock = pygame.time.Clock()
            
            # Initialize game objects
            self.snake = Snake((self.grid_width // 2, self.grid_height // 2))
            self.food = Food((self.grid_width, self.grid_height), self.snake.body)
            self.score = 0
            self.game_over = False
            
            # Font for text rendering
            self.font = pygame.font.Font(None, 36)
            
            logger.info("Game initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize game: {e}")
            raise
            
    def handle_events(self) -> None:
        """Handle user input events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                logger.info("User requested quit")
                pygame.quit()
                sys.exit()
                
            elif event.type == pygame.KEYDOWN:
                if self.game_over and event.key == pygame.K_SPACE:
                    # Restart game
                    self.restart_game()
                elif not self.game_over:
                    if event.key == pygame.K_UP:
                        self.snake.change_direction(Direction.UP)
                    elif event.key == pygame.K_DOWN:
                        self.snake.change_direction(Direction.DOWN)
                    elif event.key == pygame.K_LEFT:
                        self.snake.change_direction(Direction.LEFT)
                    elif event.key == pygame.K_RIGHT:
                        self.snake.change_direction(Direction.RIGHT)
                        
    def update(self) -> None:
        """Update game state"""
        if self.game_over:
            return
            
        # Move the snake
        self.snake.move()
        
        # Check for collisions with food
        if self.snake.get_head() == self.food.position:
            self.snake.grow()
            self.food.respawn(self.snake.body)
            self.score += 10
            logger.debug(f"Food eaten! Score: {self.score}")
            
        # Check for collisions with walls or self
        head = self.snake.get_head()
        if (head[0] < 0 or head[0] >= self.grid_width or 
            head[1] < 0 or head[1] >= self.grid_height or
            self.snake.collides_with_self()):
            self.game_over = True
            logger.info("Game over: Snake collided with wall or itself")
            
    def draw(self) -> None:
        """Draw the game state"""
        # Clear screen
        self.screen.fill((0, 0, 0))
        
        # Draw snake
        for i, (x, y) in enumerate(self.snake.body):
            color = (0, 255, 0) if i == 0 else (0, 200, 0)  # Head is brighter
            rect = pygame.Rect(x * self.cell_size, y * self.cell_size, 
                             self.cell_size, self.cell_size)
            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, (0, 100, 0), rect, 1)  # Border
            
        # Draw food
        x, y = self.food.position
        rect = pygame.Rect(x * self.cell_size, y * self.cell_size, 
                         self.cell_size, self.cell_size)
        pygame.draw.rect(self.screen, (255, 0, 0), rect)
        pygame.draw.rect(self.screen, (150, 0, 0), rect, 1)  # Border
        
        # Draw score
        score_text = self.font.render(f"Score: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (10, 10))
        
        # Draw game over message
        if self.game_over:
            game_over_text = self.font.render("GAME OVER! Press SPACE to restart", True, (255, 255, 255))
            text_rect = game_over_text.get_rect(center=(self.width // 2, self.height // 2))
            self.screen.blit(game_over_text, text_rect)
            
        pygame.display.flip()
        
    def restart_game(self) -> None:
        """Restart the game"""
        self.snake = Snake((self.grid_width // 2, self.grid_height // 2))
        self.food = Food((self.grid_width, self.grid_height), self.snake.body)
        self.score = 0
        self.game_over = False
        logger.info("Game restarted")
        
    def run(self) -> None:
        """Main game loop"""
        try:
            running = True
            while running:
                self.handle_events()
                self.update()
                self.draw()
                self.clock.tick(10)  # Control game speed
                
        except Exception as e:
            logger.error(f"Error in game loop: {e}")
            raise
            
    def __del__(self):
        """Cleanup when object is destroyed"""
        try:
            pygame.quit()
        except:
            pass

def main() -> None:
    """Main entry point for the snake game"""
    try:
        logger.info("Starting Snake Game")
        game = Game()
        game.run()
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()