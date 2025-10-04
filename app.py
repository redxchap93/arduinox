```python
import pygame
import sys
import random
import logging
import math
from typing import Tuple, List, Optional
from dataclasses import dataclass
from enum import Enum

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
BACKGROUND_COLOR = (10, 10, 20)
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

class GameState(Enum):
    MENU = "menu"
    PLAYING = "playing"
    GAME_OVER = "game_over"

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
        self.max_health = 100
        self.health = self.max_health
        self.score = 0
        self.level = 1
        self.experience = 0
        self.shoot_power = 1
    
    def update(self):
        super().update()
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
    
    def shoot(self, target_pos: Position) -> Optional[object]:
        if self.shoot_cooldown <= 0:
            self.shoot_cooldown = 15 // self.level  # Faster shooting at higher levels
            dx = target_pos.x - (self.position.x + self.size/2)
            dy = target_pos.y - (self.position.y + self.size/2)
            distance = max(1, math.sqrt(dx*dx + dy*dy))
            dx /= distance
            dy /= distance
            
            # Create projectile with enhanced properties based on level
            projectile = Projectile(
                Position(self.position.x + self.size/2, self.position.y + self.size/2),
                Velocity(dx * PROJECTILE_SPEED * self.shoot_power, dy * PROJECTILE_SPEED * self.shoot_power),
                self.level
            )
            return projectile
        return None
    
    def draw(self, screen):
        # Draw player with health bar
        super().draw(screen)
        pygame.draw.rect(screen, (0, 100, 0), 
                        (self.position.x, self.position.y - 10, self.size, 5))
        pygame.draw.rect(screen, (255, 0, 0), 
                        (self.position.x, self.position.y - 10, 
                         self.size * self.health / self.max_health, 5))
        
        # Draw level indicator
        font = pygame.font.Font(None, 24)
        level_text = font.render(f"Lv.{self.level}", True, TEXT_COLOR)
        screen.blit(level_text, (self.position.x + self.size/2 - 10, self.position.y - 25))

class Enemy(GameObject):
    def __init__(self, position: Position):
        super().__init__(position, ENEMY_SIZE)
        self.color = ENEMY_COLOR
        self.max_health = 30
        self.health = self.max_health
        self.speed = ENEMY_SPEED
        self.shoot_cooldown = 0
        self.damage = 10
        self.reward = 10
    
    def update(self):
        super().update()
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
    
    def shoot(self, target_pos: Position) -> Optional[object]:
        if self.shoot_cooldown <= 0:
            self.shoot_cooldown = random.randint(60, 120)  # Random shooting cooldown
            dx = target_pos.x - (self.position.x + self.size/2)
            dy = target_pos.y - (self.position.y + self.size/2)
            distance = max(1, math.sqrt(dx*dx + dy*dy))
            dx /= distance
            dy /= distance
            
            projectile = Projectile(
                Position(self.position.x + self.size/2, self.position.y + self.size/2),
                Velocity(dx * PROJECTILE_SPEED, dy * PROJECTILE_SPEED),
                0  # Enemy projectiles don't have level
            )
            return projectile
        return None

class Projectile(GameObject):
    def __init__(self, position: Position, velocity: Velocity, level: int = 0):
        super().__init__(position, PROJECTILE_SIZE)
        self.velocity = velocity
        self.level = level
        self.damage = max(1, 5 + level * 2)  # Damage increases with level
        self.lifetime = 300  # Frames until projectile disappears
        self.size = PROJECTILE_SIZE + level  # Larger projectiles at higher levels
    
    def update(self):
        super().update()
        self.lifetime -= 1
        if self.lifetime <= 0:
            self.alive = False

class Particle:
    def __init__(self, x: float, y: float, color: Tuple[int, int, int], size: int = 3):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.lifetime = random.randint(20, 50)
        self.vx = random.uniform(-2, 2)
        self.vy = random.uniform(-2, 2)
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.lifetime -= 1
        self.size = max(0, self.size - 0.1)
    
    def draw(self, screen):
        if self.lifetime > 0:
            pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.size))

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("AI vs AI Battle")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.particles: List[Particle] = []
        self.state = GameState.MENU
        self.player = None
        self.enemies: List[Enemy] = []
        self.projectiles: List[Projectile] = []
        self.spawn_timer = 0
        self.wave_number = 1
        self.score = 0
        self.high_score = 0
    
    def setup(self):
        """Initialize game objects"""
        self.player = Player(Position(SCREEN_WIDTH/2, SCREEN_HEIGHT/2))
        self.enemies.clear()
        self.projectiles.clear()
        self.particles.clear()
        self.spawn_timer = 0
        self.wave_number = 1
        self.score = 0
    
    def spawn_enemies(self):
        """Spawn new enemies for current wave"""
        if len(self.enemies) < MAX_ENEMIES and self.spawn_timer <= 0:
            # Spawn from edges with increasing difficulty
            side = random.choice(['top', 'bottom', 'left', 'right'])
            if side == 'top':
                pos = Position(random.randint(0, SCREEN_WIDTH), -ENEMY_SIZE)
            elif side == 'bottom':
                pos = Position(random.randint(0, SCREEN_WIDTH), SCREEN_HEIGHT)
            elif side == 'left':
                pos = Position(-ENEMY_SIZE, random.randint(0, SCREEN_HEIGHT))
            else:  # right
                pos = Position(SCREEN_WIDTH, random.randint(0, SCREEN_HEIGHT))
            
            enemy = Enemy(pos)
            # Increase difficulty with wave number
            enemy.max_health += self.wave_number * 5
            enemy.health = enemy.max_health
            enemy.speed += self.wave_number * 0.2
            enemy.reward = max(10, 10 + self.wave_number * 2)
            
            self.enemies.append(enemy)
            self.spawn_timer = max(10, SPAWN_RATE - self.wave_number * 5)  # Spawn faster as waves progress
        elif self.spawn_timer > 0:
            self.spawn_timer -= 1
    
    def update_player_ai(self):
        """Simple AI for player movement"""
        if not self.player or self.player.health <= 0:
            return
            
        # Move toward nearest enemy with some randomness
        if self.enemies:
            nearest_enemy = min(self.enemies, key=lambda e: 
                              math.sqrt((e.position.x - self.player.position.x)**2 + 
                                       (e.position.y - self.player.position.y)**2))
            
            dx = nearest_enemy.position.x - self.player.position.x
            dy = nearest_enemy.position.y - self.player.position.y
            
            # Normalize and apply speed
            distance = max(1, math.sqrt(dx*dx + dy*dy))
            dx /= distance
            dy /= distance
            
            self.player.velocity.dx = dx * PLAYER_SPEED
            self.player.velocity.dy = dy * PLAYER_SPEED
            
            # Shoot at enemy when close enough
            if distance < 200 and random.randint(1, 30) == 1:
                projectile = self.player.shoot(Position(nearest_enemy.position.x + ENEMY_SIZE/2,
                                                       nearest_enemy.position.y + ENEMY_SIZE/2))
                if projectile:
                    self.projectiles.append(projectile)
        else:
            # Random movement when no enemies
            self.player.velocity.dx = random.uniform(-PLAYER_SPEED, PLAYER_SPEED)
            self.player.velocity.dy = random.uniform(-PLAYER_SPEED, PLAYER_SPEED)
    
    def update_enemy_ai(self):
        """Simple AI for enemies"""
        if not self.player or self.player.health <= 0:
            return
            
        for enemy in self.enemies:
            # Move toward player
            dx = (self.player.position.x + PLAYER_SIZE/2) - (enemy.position.x + ENEMY_SIZE/2)
            dy = (self.player.position.y + PLAYER_SIZE/2) - (enemy.position.y + ENEMY_SIZE/2)
            
            distance = max(1, math.sqrt(dx*dx + dy*dy))
            if distance > 0:
                dx /= distance
                dy /= distance
                
                enemy.velocity.dx = dx * enemy.speed
                enemy.velocity.dy = dy * enemy.speed
            
            # Occasionally shoot at player
            if random.randint(1, 60) == 1 and enemy.shoot_cooldown <= 0:
                projectile = enemy.shoot(Position(self.player.position.x + PLAYER_SIZE/2,
                                                 self.player.position.y + PLAYER_SIZE/2))
                if projectile:
                    self.projectiles.append(projectile)
    
    def update_projectiles(self):
        """Update all projectiles"""
        for projectile in self.projectiles[:]:  # Iterate over a copy
            projectile.update()
            if not projectile.alive:
                self.projectiles.remove(projectile)
    
    def check_collisions(self):
        """Check for collisions between game objects"""
        if not self.player or self.player.health <= 0:
            return
            
        # Player vs enemies
        for enemy in self.enemies[:]:
            distance = math.sqrt((enemy.position.x - self.player.position.x)**2 + 
                               (enemy.position.y - self.player.position.y)**2)
            if distance < (self.player.size/2 + enemy.size/2):
                self.player.health -= enemy.damage
                # Create explosion particles
                for _ in range(10):
                    self.particles.append(Particle(
                        enemy.position.x + enemy.size/2,
                        enemy.position.y + enemy.size/2,
                        (255, 0, 0)
                    ))
                self.enemies.remove(enemy)
                
                # Add score and check for level up
                self.score += enemy.reward
                if self.score > self.high_score:
                    self.high_score = self.score
                
                # Level up every 100 points
                new_level = self.score // 100 + 1
                if new_level > self.player.level:
                    self.player.level = new_level
                    self.player.max_health += 20
                    self.player.health = self.player.max_health
        
        # Projectiles vs player
        for projectile in self.projectiles[:]:
            if projectile.level == 0:  # Enemy projectile
                distance = math.sqrt((projectile.position.x - self.player.position.x)**2 + 
                                   (projectile.position.y - self.player.position.y)**2)
                if distance < (self.player.size/2 + projectile.size/2):
                    self.player.health -= projectile.damage
                    self.projectiles.remove(projectile)
                    # Create hit particles
                    for _ in range(5):
                        self.particles.append(Particle(
                            projectile.position.x,
                            projectile.position.y,
                            (255, 255, 0)
                        ))
        
        # Projectiles vs enemies
        for enemy in self.enemies[:]:
            for projectile in self.projectiles[:]:
                if projectile.level > 0:  # Player projectile
                    distance = math.sqrt((projectile.position.x - enemy.position.x)**2 + 
                                       (projectile.position.y - enemy.position.y)**2)
                    if distance < (enemy.size/2 + projectile.size/2):
                        enemy.health -= projectile.damage
                        self.projectiles.remove(projectile)
                        # Create hit particles
                        for _ in range(5):
                            self.particles.append(Particle(
                                projectile.position.x,
                                projectile.position.y,
                                (0, 255, 0)
                            ))
                        if enemy.health <= 0:
                            self.enemies.remove(enemy)
                            self.score += enemy.reward
                            # Create explosion particles
                            for _ in range(15):
                                self.particles.append(Particle(
                                    enemy.position.x + enemy.size/2,
                                    enemy.position.y + enemy.size/2,
                                    (255, 0, 0)
                                ))
    
    def update_particles(self):
        """Update and draw particles"""
        for particle in self.particles[:]:
            particle.update()
            if particle.lifetime <= 0:
                self.particles.remove(particle)
    
    def update(self):
        """Main game update loop"""
        if self.state == GameState.MENU:
            # Simple menu logic - start game when space is pressed
            pass
        elif self.state == GameState.PLAYING:
            self.update_player_ai()
            self.update_enemy_ai()
            self.spawn_enemies()
            self.update_projectiles()
            self.check_collisions()
            self.update_particles()
            
            # Check if wave is complete
            if not self.enemies and self.spawn_timer <= 0:
                self.wave_number += 1
                self.spawn_timer = 60  # Start next wave after delay
    
    def draw_menu(self):
        """Draw main menu"""
        self.screen.fill((0, 0, 0))
        title_text = self.font.render("AI vs AI BATTLE", True, (255, 255, 255))
        start_text = self.small_font.render("Press SPACE to Start", True, (255, 255, 255))
        high_score_text = self.small_font.render(f"High Score: {self.high_score}", True, (255, 255, 255))
        
        self.screen.blit(title_text, (SCREEN_WIDTH/2 - title_text.get_width()/2, 100))
        self.screen.blit(start_text, (SCREEN_WIDTH/2 - start_text.get_width()/2, 200))
        self.screen.blit(high_score_text, (SCREEN_WIDTH/2 - high_score_text.get_width()/2, 250))
    
    def draw_game(self):
        """Draw game elements"""
        self.screen.fill((0, 0, 0))
        
        # Draw particles
        for particle in self.particles:
            particle.draw(self.screen)
        
        # Draw player
        if self.player and self.player.health > 0:
            self.player.draw(self.screen)
        
        # Draw enemies
        for enemy in self.enemies:
            pygame.draw.rect(self.screen, enemy.color, 
                           (enemy.position.x, enemy.position.y, enemy.size, enemy.size))
            # Health bar for enemies
            pygame.draw.rect(self.screen, (0, 100, 0), 
                           (enemy.position.x, enemy.position.y - 8, enemy.size, 4))
            pygame.draw.rect(self.screen, (255, 0, 0), 
                           (enemy.position.x, enemy.position.y - 8, 
                            enemy.size * enemy.health / enemy.max_health, 4))
        
        # Draw projectiles
        for projectile in self.projectiles:
            color = (255, 255, 0) if projectile.level > 0 else (255, 0, 0)
            pygame.draw.circle(self.screen, color, 
                             (int(projectile.position.x), int(projectile.position.y)), 
                             projectile.size)
        
        # Draw UI
        score_text = self.small_font.render(f"Score: {self.score}", True, (255, 255, 255))
        wave_text = self.small_font.render(f"Wave: {self.wave_number}", True, (255, 255, 255))
        health_text = self.small_font.render(f"Health: {self.player.health}", True, (255, 255, 255))
        
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(wave_text, (10, 35))
        self.screen.blit(health_text, (10, 60))
    
    def draw_game_over(self):
        """Draw game over screen"""
        self.screen.fill((0, 0, 0))
        game_over_text = self.font.render("GAME OVER", True, (255, 0, 0))
        score_text = self.small_font.render(f"Final Score: {self.score}", True, (255, 255, 255))
        high_score_text = self.small_font.render(f"High Score: {self.high_score}", True, (255, 255, 255))
        restart_text = self.small_font.render("Press R to Restart", True, (255, 255, 255))
        
        self.screen.blit(game_over_text, (SCREEN_WIDTH/2 - game_over_text.get_width()/2, 100))
        self.screen.blit(score_text, (SCREEN_WIDTH/2 - score_text.get_width()/2, 200))
        self.screen.blit(high_score_text, (SCREEN_WIDTH/2 - high_score_text.get_width()/2, 230))
        self.screen.blit(restart_text, (SCREEN_WIDTH/2 - restart_text.get_width()/2, 300))
    
    def run(self):
        """Main game loop"""
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and self.state == GameState.MENU:
                        self.state = GameState.PLAYING
                        self.setup()
                    elif event.key == pygame.K_r and self.state == GameState.PLAYING:
                        self.state = GameState.MENU
                    elif event.key == pygame.K_ESCAPE:
                        running = False
            
            # Update game state
            if self.state == GameState.PLAYING:
                self.update()
                
                # Check for game over condition
                if self.player and self.player.health <= 0:
                    self.state = GameState.PLAYING  # Continue showing game over screen
            
            # Draw everything
            if self.state == GameState.MENU:
                self.draw_menu()
            elif self.state == GameState.PLAYING:
                self.draw_game()
            else:
                self.draw_game_over()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()

def main():
    game = Game()
    game.run()

if __name__ == "__main__":
    main()