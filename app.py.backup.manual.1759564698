import pygame
import sys
import logging
import random
from typing import Tuple, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize pygame
try:
    pygame.init()
except pygame.error as e:
    logger.error(f"Failed to initialize pygame: {e}")
    sys.exit(1)

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE
FPS = 10

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
DARK_GREEN = (0, 200, 0)

class Snake:
    """Represents the snake in the game."""
    
    def __init__(self):
        self.reset()
        
    def reset(self):
        """Reset the snake to initial state."""
        self.length = 3
        self.positions = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
        self.score = 0
        self.grow_pending = 2  # Start with 3 segments
        
    def get_head_position(self) -> Tuple[int, int]:
        """Get the position of the snake's head."""
        return self.positions[0]
        
    def update(self) -> bool:
        """Update the snake's position and check for collisions."""
        head = self.get_head_position()
        x, y = self.direction
        new_position = (((head[0] + x) % GRID_WIDTH), ((head[1] + y) % GRID_HEIGHT))
        
        # Check for collision with self
        if new_position in self.positions[1:]:
            return False
            
        self.positions.insert(0, new_position)
        
        if self.grow_pending > 0:
            self.grow_pending -= 1
        else:
            self.positions.pop()
            
        return True
        
    def grow(self):
        """Increase the snake's length."""
        self.grow_pending += 1
        self.score += 10
        
    def render(self, surface):
        """Draw the snake on the game surface."""
        for i, pos in enumerate(self.positions):
            # Draw snake segment
            rect = pygame.Rect(pos[0] * GRID_SIZE, pos[1] * GRID_SIZE, GRID_SIZE, GRID_SIZE)
            if i == 0:  # Head
                pygame.draw.rect(surface, DARK_GREEN, rect)
                pygame.draw.rect(surface, BLACK, rect, 1)
            else:  # Body
                pygame.draw.rect(surface, GREEN, rect)
                pygame.draw.rect(surface, BLACK, rect, 1)

class Food:
    """Represents the food in the game."""
    
    def __init__(self):
        self.position = (0, 0)
        self.randomize_position()
        
    def randomize_position(self):
        """Generate a random position for the food."""
        self.position = (random.randint(0, GRID_WIDTH - 1), random.randint(0, GRID_HEIGHT - 1))
        
    def render(self, surface):
        """Draw the food on the game surface."""
        rect = pygame.Rect(
            self.position[0] * GRID_SIZE,
            self.position[1] * GRID_SIZE,
            GRID_SIZE, GRID_SIZE
        )
        pygame.draw.rect(surface, RED, rect)
        pygame.draw.rect(surface, BLACK, rect, 1)

class Game:
    """Main game class that manages the game state."""
    
    def __init__(self):
        try:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption("Snake Game")
            self.clock = pygame.time.Clock()
            self.font = pygame.font.Font(None, 36)
            self.snake = Snake()
            self.food = Food()
            self.game_over = False
        except pygame.error as e:
            logger.error(f"Failed to initialize game: {e}")
            raise
            
    def handle_events(self):
        """Handle user input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if self.game_over and event.key == pygame.K_SPACE:
                    self.snake.reset()
                    self.food.randomize_position()
                    self.game_over = False
                elif not self.game_over:
                    if event.key == pygame.K_UP and self.snake.direction != (0, 1):
                        self.snake.direction = (0, -1)
                    elif event.key == pygame.K_DOWN and self.snake.direction != (0, -1):
                        self.snake.direction = (0, 1)
                    elif event.key == pygame.K_LEFT and self.snake.direction != (1, 0):
                        self.snake.direction = (-1, 0)
                    elif event.key == pygame.K_RIGHT and self.snake.direction != (-1, 0):
                        self.snake.direction = (1, 0)
        return True
        
    def update(self):
        """Update game state."""
        if self.game_over:
            return
            
        # Update snake position
        if not self.snake.update():
            self.game_over = True
            return
            
        # Check for food collision
        if self.snake.get_head_position() == self.food.position:
            self.snake.grow()
            self.food.randomize_position()
            # Make sure food doesn't appear on snake
            while self.food.position in self.snake.positions:
                self.food.randomize_position()
                
    def render(self):
        """Draw everything to the screen."""
        self.screen.fill(BLACK)
        
        if not self.game_over:
            self.snake.render(self.screen)
            self.food.render(self.screen)
            
            # Draw score
            score_text = self.font.render(f"Score: {self.snake.score}", True, WHITE)
            self.screen.blit(score_text, (10, 10))
        else:
            # Draw game over screen
            game_over_text = self.font.render("GAME OVER", True, WHITE)
            restart_text = self.font.render("Press SPACE to restart", True, WHITE)
            
            game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 20))
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
            
            self.screen.blit(game_over_text, game_over_rect)
            self.screen.blit(restart_text, restart_rect)
            
        pygame.display.flip()
        
    def run(self):
        """Main game loop."""
        running = True
        try:
            while running:
                running = self.handle_events()
                self.update()
                self.render()
                self.clock.tick(FPS)
        except Exception as e:
            logger.error(f"Error in game loop: {e}")
            raise
        finally:
            pygame.quit()

def main():
    """Main entry point for the application."""
    try:
        logger.info("Starting Snake Game")
        game = Game()
        game.run()
        logger.info("Snake Game ended")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()