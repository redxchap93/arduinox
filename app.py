import pygame
import sys
import random
import logging
import math
from typing import Tuple, List, Optional
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_game.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
FPS = 60
BACKGROUND_COLOR = (20, 20, 30)
PLAYER_COLOR = (0, 200, 255)
ENEMY_COLOR = (255, 50, 50)
PROJECTILE_COLOR = (255, 255, 100)
TEXT_COLOR = (255, 255, 255)
PLAYER_SIZE = 30
ENEMY_SIZE = 25
PROJECTILE_SIZE = 5
PLAYER_SPEED = 5
ENEMY_SPEED = 3
PROJECTILE_SPEED = 8
MAX_PROJECTILES = 10
SPAWN_RATE = 60  # frames between enemy spawns
MAX_ENEMIES = 15

@dataclass
class Position:
    x: float
    y: float

@dataclass
class Velocity:
    dx: float
    dy: float

class GameObject:
    def __init__(self, position: Position, size: int):
        self.position = position
        self.size = size
        self.velocity = Velocity(0, 0)
        self.alive = True
    
    def update(self):
        self.position.x += self.velocity.dx
        self.position.y += self.velocity.dy
        
        # Keep within bounds
        if self.position.x < 0:
            self.position.x = 0
        elif self.position.x > SCREEN_WIDTH - self.size:
            self.position.x = SCREEN_WIDTH - self.size
            
        if self.position.y < 0:
            self.position.y = 0
        elif self.position.y > SCREEN_HEIGHT - self.size:
            self.position.y = SCREEN_HEIGHT - self.size
    
    def draw(self, screen):
        pygame.draw.rect(screen, (255, 255, 255), 
                        (self.position.x, self.position.y, self.size, self.size), 2)
    
    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.position.x, self.position.y, self.size, self.size)

class Player(GameObject):
    def __init__(self, position: Position):
        super().__init__(position, PLAYER_SIZE)
        self.color = PLAYER_COLOR
        self.shoot_cooldown = 0
    
    def update(self):
        super().update()
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
    
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, 
                        (self.position.x, self.position.y, self.size, self.size))
        # Draw a simple indicator
        pygame.draw.circle(screen, (255, 255, 255), 
                          (int(self.position.x + self.size/2), int(self.position.y + self.size/2)), 
                          8, 2)
    
    def shoot(self, target: Position) -> Optional['Projectile']:
        if self.shoot_cooldown <= 0:
            self.shoot_cooldown = 15
            direction = pygame.Vector2(target.x - (self.position.x + self.size/2),
                                     target.y - (self.position.y + self.size/2))
            direction.scale_to_length(PROJECTILE_SPEED)
            
            projectile_pos = Position(self.position.x + self.size/2, self.position.y + self.size/2)
            return Projectile(projectile_pos, direction)
        return None

class Enemy(GameObject):
    def __init__(self, position: Position):
        super().__init__(position, ENEMY_SIZE)
        self.color = ENEMY_COLOR
        self.shoot_cooldown = random.randint(30, 120)  # Random initial cooldown
    
    def update(self):
        super().update()
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
    
    def draw(self, screen):
        pygame.draw.rect(screen, self.color, 
                        (self.position.x, self.position.y, self.size, self.size))
        # Draw a simple indicator
        pygame.draw.circle(screen, (255, 255, 255), 
                          (int(self.position.x + self.size/2), int(self.position.y + self.size/2)), 
                          6, 1)
    
    def shoot(self, target: Position) -> Optional['Projectile']:
        if self.shoot_cooldown <= 0:
            self.shoot_cooldown = random.randint(60, 180)
            direction = pygame.Vector2(target.x - (self.position.x + self.size/2),
                                     target.y - (self.position.y + self.size/2))
            direction.scale_to_length(PROJECTILE_SPEED)
            
            projectile_pos = Position(self.position.x + self.size/2, self.position.y + self.size/2)
            return Projectile(projectile_pos, direction)
        return None

class Projectile(GameObject):
    def __init__(self, position: Position, velocity: Velocity):
        super().__init__(position, PROJECTILE_SIZE)
        self.velocity = velocity
        self.color = PROJECTILE_COLOR
    
    def update(self):
        super().update()
        # Remove if out of bounds
        if (self.position.x < -self.size or self.position.x > SCREEN_WIDTH + self.size or
            self.position.y < -self.size or self.position.y > SCREEN_HEIGHT + self.size):
            self.alive = False
    
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, 
                          (int(self.position.x), int(self.position.y)), 
                          self.size)

class Game:
    def __init__(self):
        self.screen = None
        self.clock = None
        self.running = False
        
        # Game objects
        self.player = None
        self.enemies: List[Enemy] = []
        self.projectiles: List[Projectile] = []
        self.spawn_timer = 0
        self.score = 0
        self.game_over = False
        
        # Initialize Pygame
        try:
            pygame.init()
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption("AI vs AI Battle")
            self.clock = pygame.time.Clock()
            logger.info("Pygame initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Pygame: {e}")
            raise
    
    def setup(self):
        """Initialize game objects"""
        try:
            # Create player at center
            self.player = Player(Position(SCREEN_WIDTH/2 - PLAYER_SIZE/2, SCREEN_HEIGHT/2 - PLAYER_SIZE/2))
            
            # Clear lists
            self.enemies.clear()
            self.projectiles.clear()
            
            # Reset game state
            self.score = 0
            self.game_over = False
            self.spawn_timer = 0
            
            logger.info("Game setup completed")
        except Exception as e:
            logger.error(f"Failed to setup game: {e}")
            raise
    
    def handle_events(self):
        """Handle pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_r and self.game_over:
                    self.setup()
    
    def update_player_ai(self):
        """Simple AI for player movement"""
        try:
            # Move towards center of enemies
            if not self.enemies:
                return
            
            # Calculate average position of enemies
            avg_x = sum(enemy.position.x for enemy in self.enemies) / len(self.enemies)
            avg_y = sum(enemy.position.y for enemy in self.enemies) / len(self.enemies)
            
            # Move towards enemies with some randomness
            dx = avg_x - (self.player.position.x + PLAYER_SIZE/2)
            dy = avg_y - (self.player.position.y + PLAYER_SIZE/2)
            
            # Normalize and apply speed
            distance = math.sqrt(dx*dx + dy*dy)
            if distance > 0:
                dx /= distance
                dy /= distance
                
                self.player.velocity.dx = dx * PLAYER_SPEED * 0.7
                self.player.velocity.dy = dy * PLAYER_SPEED * 0.7
            
            # Random movement for unpredictability
            self.player.velocity.dx += random.uniform(-0.5, 0.5)
            self.player.velocity.dy += random.uniform(-0.5, 0.5)
            
            # Keep within bounds
            if abs(self.player.velocity.dx) > PLAYER_SPEED:
                self.player.velocity.dx = math.copysign(PLAYER_SPEED, self.player.velocity.dx)
            if abs(self.player.velocity.dy) > PLAYER_SPEED:
                self.player.velocity.dy = math.copysign(PLAYER_SPEED, self.player.velocity.dy)
                
        except Exception as e:
            logger.error(f"Error in player AI update: {e}")
    
    def update_enemy_ai(self):
        """Simple AI for enemies"""
        try:
            if not self.player:
                return
            
            # Each enemy moves toward the player
            for enemy in self.enemies:
                dx = (self.player.position.x + PLAYER_SIZE/2) - (enemy.position.x + ENEMY_SIZE/2)
                dy = (self.player.position.y + PLAYER_SIZE/2) - (enemy.position.y + ENEMY_SIZE/2)
                
                # Normalize and apply speed
                distance = math.sqrt(dx*dx + dy*dy)
                if distance > 0:
                    dx /= distance
                    dy /= distance
                    
                    enemy.velocity.dx = dx * ENEMY_SPEED
                    enemy.velocity.dy = dy * ENEMY_SPEED
                
                # Occasionally shoot at player
                if random.randint(1, 60) == 1:  # 1 in 60 chance each frame
                    projectile = enemy.shoot(Position(self.player.position.x + PLAYER_SIZE/2,
                                                     self.player.position.y + PLAYER_SIZE/2))
                    if projectile:
                        self.projectiles.append(projectile)
                        
        except Exception as e:
            logger.error(f"Error in enemy AI update: {e}")
    
    def spawn_enemies(self):
        """Spawn new enemies"""
        try:
            if len(self.enemies) < MAX_ENEMIES and self.spawn_timer <= 0:
                # Spawn from edges
                side = random.choice(['top', 'bottom', 'left', 'right'])
                if side == 'top':
                    pos = Position(random.randint(0, SCREEN_WIDTH), -ENEMY_SIZE)
                elif side == 'bottom':
                    pos = Position(random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT)
                elif side == 'left':
                    pos = Position(-ENEMY_SIZE, random.randint(0, SCREEN_HEIGHT))
                else:  # right
                    pos = Position(SCREEN_WIDTH, random.randint(0, SCREEN_HEIGHT))
                
                self.enemies.append(Enemy(pos))
                self.spawn_timer = SPAWN_RATE
            elif self.spawn_timer > 0:
                self.spawn_timer -= 1
                
        except Exception as e:
            logger.error(f"Error spawning enemies: {e}")
    
    def update_projectiles(self):
        """Update all projectiles"""
        try:
            for projectile in self.projectiles[:]:  # Iterate over a copy
                projectile.update()
                if not projectile.alive:
                    self.projectiles.remove(projectile)
                    
        except Exception as e:
            logger.error(f"Error updating projectiles: {e}")
    
    def check_collisions(self):
        """Check for collisions between game objects"""
        try:
            # Player vs enemies
            if self.player:
                player_rect = self.player.get_rect()
                for enemy in self.enemies[:]:  # Iterate over a copy
                    if player_rect.colliderect(enemy.get_rect()):
                        # Collision with enemy - game over
                        self.game_over = True
                        logger.info("Game Over: Player hit by enemy")
            
            # Projectiles vs enemies
            for projectile in self.projectiles[:]:  # Iterate over a copy
                if not projectile.alive:
                    continue
                    
                projectile_rect = projectile.get_rect()
                for enemy in self.enemies[:]:  # Iterate over a copy
                    if projectile_rect.colliderect(enemy.get_rect()):
                        # Hit enemy
                        self.enemies.remove(enemy)
                        projectile.alive = False
                        self.score += 10
                        break
                        
            # Projectiles vs player
            if self.player:
                player_rect = self.player.get_rect()
                for projectile in self.projectiles[:]:  # Iterate over a copy
                    if projectile_rect.colliderect(player_rect):
                        # Hit player - game over
                        self.game_over = True
                        logger.info("Game Over: Player hit by projectile")
                        projectile.alive = False
                        
        except Exception as e:
            logger.error(f"Error checking collisions: {e}")
    
    def update(self):
        """Update game state"""
        try:
            if self.game_over:
                return
                
            # Update AI
            self.update_player_ai()
            self.update_enemy_ai()
            
            # Spawn enemies
            self.spawn_enemies()
            
            # Update all objects
            self.player.update()
            for enemy in self.enemies:
                enemy.update()
            self.update_projectiles()
            
            # Check collisions
            self.check_collisions()
            
        except Exception as e:
            logger.error(f"Error updating game: {e}")
    
    def draw(self):
        """Draw everything"""
        try:
            # Clear screen
            self.screen.fill(BACKGROUND_COLOR)
            
            # Draw game objects
            if self.player:
                self.player.draw(self.screen)
                
            for enemy in self.enemies:
                enemy.draw(self.screen)
                
            for projectile in self.projectiles:
                projectile.draw(self.screen)
            
            # Draw UI
            font = pygame.font.Font(None, 36)
            score_text = font.render(f"Score: {self.score}", True, TEXT_COLOR)
            self.screen.blit(score_text, (10, 10))
            
            if self.game_over:
                game_over_font = pygame.font.Font(None, 72)
                game_over_text = game_over_font.render("GAME OVER", True, (255, 50, 50))
                restart_text = font.render("Press R to Restart", True, TEXT_COLOR)
                
                text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 - 30))
                restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH/2, SCREEN_HEIGHT/2 + 30))
                
                self.screen.blit(game_over_text, text_rect)
                self.screen.blit(restart_text, restart_rect)
            
            pygame.display.flip()
            
        except Exception as e:
            logger.error(f"Error drawing game: {e}")
    
    def run(self):
        """Main game loop"""
        try:
            self.running = True
            self.setup()
            
            while self.running:
                self.handle_events()
                self.update()
                self.draw()
                self.clock.tick(FPS)
                
        except Exception as e:
            logger.error(f"Error in main game loop: {e}")
            raise
        finally:
            pygame.quit()
            logger.info("Game terminated")

def main():
    """Main entry point"""
    try:
        logger.info("Starting AI vs AI Battle game")
        game = Game()
        game.run()
        logger.info("Game completed successfully")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()