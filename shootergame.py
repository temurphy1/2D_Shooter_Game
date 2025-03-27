import pygame
import math
import random
import time
import numpy as np
import os

# Initialize Pygame
pygame.init()

# Set up the game window
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 800
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("2D Paintball Shooter")

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 255, 0)
PURPLE = (128, 0, 128)  # Add purple color

# Paintball properties
class Paintball:
    """
    Class representing paintballs shot by the player
    Each paintball is a projectile that moves in a straight line with some variance
    """
    def __init__(self, x, y, angle, max_range, speed=50):
        self.radius = 5                # Size of the paintball
        self.x = x                     # Current X position
        self.y = y                     # Current Y position
        self.start_x = x               # Starting X position (for distance calculation)
        self.start_y = y               # Starting Y position (for distance calculation)
        self.angle = angle            # Direction of travel in radians
        self.speed = speed            # How fast the paintball moves
        self.active = True            # Whether the paintball is still in play
        self.distance_traveled = 0     # Track how far the paintball has moved
        self.max_range = max_range    # Maximum distance the paintball can travel

    def move(self):
        """Update the paintball's position and check if it should be deactivated"""
        # Store current position to calculate distance moved
        prev_x = self.x
        prev_y = self.y

        # Update position using trigonometry:
        # cos(angle) gives x component of movement
        # sin(angle) gives y component of movement
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed

        # Calculate how far the paintball moved in this step using Pythagorean theorem
        dx = self.x - prev_x
        dy = self.y - prev_y
        self.distance_traveled += math.sqrt(dx * dx + dy * dy)

        # Deactivate paintball if it:
        # 1. Goes off screen
        # 2. Exceeds its maximum range
        if (self.x < 0 or self.x > WINDOW_WIDTH or 
            self.y < 0 or self.y > WINDOW_HEIGHT or
            self.distance_traveled >= self.max_range):
            self.active = False

    def draw(self, screen):
        """Draw the paintball on the screen if it's active"""
        if self.active:
            # Draw a black circle at the paintball's position
            pygame.draw.circle(screen, BLACK, (int(self.x), int(self.y)), self.radius)

    def check_hit(self, target):
        """Check if this paintball has hit a target"""
        if not self.active:
            return False
            
        # Create rectangular collision boxes for both paintball and target
        target_rect = pygame.Rect(target.x, target.y, target.width, target.height)
        paintball_rect = pygame.Rect(self.x - self.radius, self.y - self.radius, 
                                  self.radius * 2, self.radius * 2)
        # Check if the rectangles overlap
        return target_rect.colliderect(paintball_rect)

# Add near the top with other weapon properties
MEDIUM_RANGE_VARIANCE = math.radians(2)  # 2 degrees variance for medium range
LONG_RANGE_VARIANCE = math.radians(0.5)  # 0.5 degrees variance for long range

MEDIUM_RANGE_MOVE_SPEED = 2
LONG_RANGE_MOVE_SPEED = 1

# Player class represents the user-controlled character in the game
class Player:
    def __init__(self):
        # Basic dimensions and positioning
        self.width = 20                    # Player's width in pixels
        self.height = 20                   # Player's height in pixels
        self.x = WINDOW_WIDTH // 2         # Start at horizontal center (// means integer division)
        self.y = WINDOW_HEIGHT // 2        # Start at vertical center
        self.speed = MEDIUM_RANGE_MOVE_SPEED  # Start with medium range weapon (AR-15)
        self.angle = 0                     # Direction player is facing (in radians)
        self.last_shot_time = 0            # Tracks when the last shot was fired
        self.current_weapon = "medium"     # Start with medium range weapon (AR-15)
        self.health = 100                  # Player starts with full health
        self.score = 0                     # Track number of targets destroyed

    def get_current_movement_speed(self):
        """Get the movement speed for the current weapon"""
        # AR-15 has medium range move speed
        # Sniper has long range move speed
        return MEDIUM_RANGE_MOVE_SPEED if self.current_weapon == "medium" else LONG_RANGE_MOVE_SPEED
    
    def get_current_weapon_sound(self):
        """Get the sound for the current weapon"""
        # AR-15 has medium range sound
        # Sniper has long range sound
        return paintball_sound if self.current_weapon == "medium" else long_range_sound

    def check_collision_with_targets(self, new_x, new_y):
        """Check if moving to new_x, new_y would cause collision with any targets"""
        # Create a rectangle representing where the player would be after moving
        player_rect = pygame.Rect(new_x, new_y, self.width, self.height)
        
        # Check against each active target
        for target in targets:
            if not target.hit:  # Only check non-destroyed targets
                target_rect = pygame.Rect(target.x, target.y, target.width, target.height)
                if player_rect.colliderect(target_rect):
                    return True  # Collision detected
        return False  # No collisions found

    def check_collision_with_obstacles(self, new_x, new_y):
        """Check if moving to new_x, new_y would cause collision with any obstacles"""
        # Create a rectangle representing where the player would be after moving
        player_rect = pygame.Rect(new_x, new_y, self.width, self.height)
        
        # Check against each obstacle
        for obstacle in obstacles:
            obstacle_rect = pygame.Rect(obstacle.x, obstacle.y, obstacle.width, obstacle.height)
            if player_rect.colliderect(obstacle_rect):
                return True  # Collision detected
        return False  # No collisions found

    def move(self, keys):
        """Handle player movement based on keyboard input"""
        # Store current position for collision checking
        new_x = self.x
        new_y = self.y

        # Get current speed based on weapon
        current_speed = self.get_current_movement_speed()

        # Update position based on which keys are pressed
        # Note: Negative y is up in pygame's coordinate system
        if keys[pygame.K_w]:  # W key moves up
            new_y -= current_speed
        if keys[pygame.K_s]:  # S key moves down
            new_y += current_speed
        if keys[pygame.K_a]:  # A key moves left
            new_x -= current_speed
        if keys[pygame.K_d]:  # D key moves right
            new_x += current_speed

        # Keep player within screen bounds using min/max
        # min() prevents going past right/bottom edge
        # max() prevents going past left/top edge
        new_x = max(0, min(new_x, WINDOW_WIDTH - self.width))
        new_y = max(0, min(new_y, WINDOW_HEIGHT - self.height))

        # Check and handle collisions separately for x and y
        # This allows sliding along obstacles instead of stopping completely
        if not self.check_collision_with_obstacles(new_x, self.y):
            self.x = new_x  # Update x if no collision
        if not self.check_collision_with_obstacles(self.x, new_y):
            self.y = new_y  # Update y if no collision

        # Also check for collisions with targets
        if not self.check_collision_with_targets(new_x, self.y):
            self.x = new_x  # Update x if no collision
        if not self.check_collision_with_targets(self.x, new_y):
            self.y = new_y  # Update y if no collision

    def draw(self, screen):
        """Draw the player, their gun, and health bar"""
        # Draw the player as a blue square
        pygame.draw.rect(screen, BLUE, (self.x, self.y, self.width, self.height))
        
        # Calculate center point of player for gun drawing
        center_x = self.x + self.width // 2
        center_y = self.y + self.height // 2
        
        # Get current mouse position for aiming
        mouse_x, mouse_y = pygame.mouse.get_pos()
        
        # Calculate angle between player center and mouse cursor
        # atan2 gives us the angle in radians, handling all quadrants correctly
        dx = mouse_x - center_x
        dy = mouse_y - center_y
        self.angle = math.atan2(dy, dx)
        
        # Draw the gun as a line pointing towards the mouse
        gun_length = 20
        # Use trigonometry to calculate end point of gun line
        end_x = center_x + math.cos(self.angle) * gun_length
        end_y = center_y + math.sin(self.angle) * gun_length
        # Color gun based on weapon type (black=AR-15, yellow=Sniper)
        gun_color = BLACK if self.current_weapon == "medium" else YELLOW
        pygame.draw.line(screen, gun_color, (center_x, center_y), (end_x, end_y), 3)

        # Draw health bar above player
        health_bar_width = 50
        health_bar_height = 5
        health_percentage = max(0, self.health / 100)  # Calculate how full the bar should be
        # Draw red background (empty health)
        pygame.draw.rect(screen, RED, (self.x - 15, self.y - 10, health_bar_width, health_bar_height))
        # Draw green foreground (current health)
        pygame.draw.rect(screen, GREEN, (self.x - 15, self.y - 10, 
                                       health_bar_width * health_percentage, health_bar_height))

    def can_shoot(self):
        """Check if enough time has passed to allow another shot"""
        current_time = time.time()
        # Get appropriate fire delay based on current weapon
        fire_delay = MEDIUM_RANGE_FIRE_DELAY if self.current_weapon == "medium" else LONG_RANGE_FIRE_DELAY
        
        # Check if enough time has passed since last shot
        if current_time - self.last_shot_time >= fire_delay:
            self.last_shot_time = current_time  # Reset timer
            return True
        return False

    def get_max_angle_variance(self):
        """Get the maximum angle variance for the current weapon"""
        # AR-15 has wider spread (2 degrees)
        # Sniper has tighter spread (0.5 degrees)
        return MEDIUM_RANGE_VARIANCE if self.current_weapon == "medium" else LONG_RANGE_VARIANCE

    def calculate_shot_angle(self):
        """Calculate the actual angle of the shot, including random variance"""
        # Get the maximum variance for current weapon
        max_angle_variance = self.get_max_angle_variance()
        
        # Generate random variance using normal distribution
        # Using max_variance/2 as standard deviation means ~95% of shots fall within ±max_variance
        variance = np.random.normal(0, max_angle_variance / 2)
        
        # Clamp variance to prevent extreme outliers
        variance = max(min(variance, max_angle_variance), -max_angle_variance)
        
        # Add variance to base angle
        return self.angle + variance

    def calculate_shot_damage(self):
        """Get the damage value for the current weapon"""
        # AR-15 does less damage but shoots faster
        # Sniper does more damage but shoots slower
        return MEDIUM_RANGE_DAMAGE if self.current_weapon == "medium" else LONG_RANGE_DAMAGE
        
    def get_current_range(self):
        """Get the maximum range for the current weapon"""
        # AR-15 has shorter range
        # Sniper has longer range
        return MEDIUM_RANGE_DISTANCE if self.current_weapon == "medium" else LONG_RANGE_DISTANCE

    def get_current_projectile_speed(self):
        """Get the projectile speed for the current weapon"""
        # AR-15 shoots slower projectiles
        # Sniper shoots faster projectiles
        return MEDIUM_RANGE_SPEED if self.current_weapon == "medium" else LONG_RANGE_SPEED

# Target class represents the enemy units that chase and shoot at the player
class Target:
    def __init__(self, x, y):
        # Basic dimensions and positioning
        self.width = 30                    # Target's width in pixels
        self.height = 30                   # Target's height in pixels
        self.x = x                         # Starting X position
        self.y = y                         # Starting Y position
        self.hit = False                   # Track if target has been destroyed
        
        # Shooting mechanics
        self.last_shot_time = time.time()  # Track when target last fired
        self.next_shot_delay = random.uniform(0,1)  # Random delay between shots (0-1 seconds)
        self.speed = 0.25                  # Movement speed in pixels per frame
        self.max_angle_variance = math.radians(5)  # Maximum 5 degrees spread on shots
        
        # Health system
        self.health = 100                  # Starting health
        self.max_health = 100              # Maximum possible health
        
        # Combat range
        # Target can only shoot if player is within 60% of screen size
        self.shooting_range = min(WINDOW_WIDTH, WINDOW_HEIGHT) * 0.6

    def calculate_shot_angle(self, player_x, player_y):
        """Calculate angle to shoot at player, including random variance"""
        # Find center point of target for shot origin
        start_x = self.x + self.width // 2
        start_y = self.y + self.height // 2
        
        # Calculate direction to player
        dx = player_x - start_x
        dy = player_y - start_y
        
        # Get base angle using arctangent
        # atan2 handles all quadrants correctly
        base_angle = math.atan2(dy, dx)
        
        # Add random variance to make shots less perfect
        # Using normal distribution means most shots are close to aim
        # Standard deviation of max/2 means ~95% of shots within ±max_angle_variance
        variance = np.random.normal(0, self.max_angle_variance / 2)
        
        # Clamp variance to prevent extreme outliers
        variance = max(min(variance, self.max_angle_variance), -self.max_angle_variance)
        
        return base_angle + variance

    def move_towards_player(self, player):
        """Update target position to move towards player"""
        if not self.hit:
            # Calculate centers of both target and player
            player_center_x = player.x + player.width // 2
            player_center_y = player.y + player.height // 2
            target_center_x = self.x + self.width // 2
            target_center_y = self.y + self.height // 2
            
            # Calculate direction vector to player
            dx = player_center_x - target_center_x
            dy = player_center_y - target_center_y
            
            # Normalize the direction vector (make it length 1)
            # This ensures consistent movement speed regardless of distance
            length = math.sqrt(dx * dx + dy * dy)
            if length > 0:  # Avoid division by zero
                dx = dx / length
                dy = dy / length
                
                # Calculate new position
                new_x = self.x + dx * self.speed
                new_y = self.y + dy * self.speed
                
                # Check for collisions with obstacles before moving
                target_rect = pygame.Rect(new_x, new_y, self.width, self.height)
                collision = False
                
                # Check each obstacle
                for obstacle in obstacles:
                    obstacle_rect = pygame.Rect(obstacle.x, obstacle.y, 
                                             obstacle.width, obstacle.height)
                    if target_rect.colliderect(obstacle_rect):
                        collision = True
                        break
                
                # Only update position if no collision occurred
                if not collision:
                    self.x = new_x
                    self.y = new_y

    def is_player_in_range(self, player):
        """Check if player is within shooting range"""
        # Calculate centers of target and player
        target_center_x = self.x + self.width // 2
        target_center_y = self.y + self.height // 2
        player_center_x = player.x + player.width // 2
        player_center_y = player.y + player.height // 2
        
        # Calculate distance using Pythagorean theorem
        dx = player_center_x - target_center_x
        dy = player_center_y - target_center_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        # Return True if player is within shooting range
        return distance <= self.shooting_range

    def draw(self, screen):
        """Draw the target and its health bar"""
        if not self.hit:
            # Draw target as red square
            pygame.draw.rect(screen, RED, (self.x, self.y, self.width, self.height))
            
            # Draw health bar
            health_bar_width = 30
            health_bar_height = 4
            health_percentage = max(0, self.health / self.max_health)
            
            # Draw red background (empty health)
            pygame.draw.rect(screen, RED, 
                           (self.x, self.y - 8, health_bar_width, health_bar_height))
            # Draw green foreground (current health)
            pygame.draw.rect(screen, GREEN,
                           (self.x, self.y - 8, health_bar_width * health_percentage, 
                            health_bar_height))

            # Debug feature: show shooting range (commented out by default)
            # if DEBUG_MODE:
            #     pygame.draw.circle(screen, (200, 200, 200), 
            #                       (int(self.x + self.width/2), 
            #                        int(self.y + self.height/2)), 
            #                       int(self.shooting_range), 1)

    def can_shoot(self, current_time):
        """Check if target can shoot based on time delay"""
        # Check if enough time has passed since last shot
        if current_time - self.last_shot_time >= self.next_shot_delay:
            self.last_shot_time = current_time  # Reset timer
            self.next_shot_delay = random.uniform(0, 1)  # Set new random delay
            return True
        return False

# Add after the Paintball class
class Bullet:
    """
    Class representing bullets fired by targets at the player
    Each bullet moves in a straight line towards its target point
    """
    def __init__(self, x, y, target_x, target_y, speed=50):
        self.radius = 4                # Bullets are smaller than paintballs
        self.x = x                     # Current X position
        self.y = y                     # Current Y position
        self.start_x = x               # Starting X position (for distance tracking)
        self.start_y = y               # Starting Y position
        
        # Calculate direction vector towards target point
        dx = target_x - x
        dy = target_y - y
        # Normalize the direction vector (make it length 1)
        length = math.sqrt(dx * dx + dy * dy)
        # Calculate velocity components (direction * speed)
        self.dx = dx / length * speed if length > 0 else 0
        self.dy = dy / length * speed if length > 0 else 0
        
        self.active = True             # Whether bullet is still in play
        self.distance_traveled = 0      # Track total distance moved

    def move(self):
        """Update bullet position and check if it should be deactivated"""
        # Store previous position for distance calculation
        prev_x = self.x
        prev_y = self.y

        # Move bullet using pre-calculated velocity
        self.x += self.dx
        self.y += self.dy

        # Calculate distance moved in this step
        dx = self.x - prev_x
        dy = self.y - prev_y
        self.distance_traveled += math.sqrt(dx * dx + dy * dy)

        # Deactivate bullet if it:
        # 1. Goes off screen
        # 2. Exceeds maximum range
        if (self.x < 0 or self.x > WINDOW_WIDTH or 
            self.y < 0 or self.y > WINDOW_HEIGHT or
            self.distance_traveled >= MAX_RANGE_BULLET):
            self.active = False

    def draw(self, screen):
        """Draw the bullet on screen if active"""
        if self.active:
            # Draw bullet as small red circle
            pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), self.radius)

    def check_hit_player(self, player):
        """Check if bullet has hit the player"""
        if not self.active:
            return False
        
        # Create collision rectangles for bullet and player
        player_rect = pygame.Rect(player.x, player.y, player.width, player.height)
        bullet_rect = pygame.Rect(self.x - self.radius, self.y - self.radius,
                                self.radius * 2, self.radius * 2)
        # Check if rectangles overlap
        return player_rect.colliderect(bullet_rect)

# Add this helper function after the class definitions
def get_min_spawn_distance():
    # Calculate 20% of the smallest window dimension
    return min(WINDOW_WIDTH, WINDOW_HEIGHT) * 0.4

def spawn_target(player):
    # Get minimum spawn distance
    min_distance = get_min_spawn_distance()
    
    while True:
        # Generate random position
        x = random.randint(0, WINDOW_WIDTH - 30)
        y = random.randint(0, WINDOW_HEIGHT - 30)
        
        # Calculate distance from player
        player_center_x = player.x + player.width // 2
        player_center_y = player.y + player.height // 2
        dx = x - player_center_x
        dy = y - player_center_y
        distance = math.sqrt(dx * dx + dy * dy)
        
        # If distance is greater than minimum, use this position
        if distance >= min_distance:
            return Target(x, y)

# Add new Obstacle class after other class definitions
class Obstacle:
    """
    Class representing static obstacles in the game
    Obstacles block movement and projectiles
    """
    def __init__(self, x, y):
        self.width = 60                # Width (3x player width)
        self.height = 60               # Height (3x player height)
        self.x = x                     # Position X
        self.y = y                     # Position Y

    def draw(self, screen):
        """Draw the obstacle as a purple rectangle"""
        pygame.draw.rect(screen, PURPLE, (self.x, self.y, self.width, self.height))

    def check_collision(self, x, y, radius):
        """Check if a circular object collides with this obstacle"""
        # Create rectangles for collision detection
        obstacle_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        # Create rectangle around the circular object
        object_rect = pygame.Rect(x - radius, y - radius, radius * 2, radius * 2)
        return obstacle_rect.colliderect(object_rect)

# Add after other class definitions
class Medkit:
    """
    Class representing health pickup items
    Spawns when player health is low and restores health when collected
    """
    def __init__(self, x, y):
        self.width = 20                # Same size as player
        self.height = 20
        self.x = x
        self.y = y
        self.active = True             # Whether medkit can be collected

    def draw(self, screen):
        """Draw the medkit as a white square with red cross"""
        if self.active:
            # Draw white background square
            pygame.draw.rect(screen, WHITE, (self.x, self.y, self.width, self.height))
            # Draw red cross symbol
            pygame.draw.rect(screen, RED, (self.x + 8, self.y + 2, 4, 16))  # Vertical
            pygame.draw.rect(screen, RED, (self.x + 2, self.y + 8, 16, 4))  # Horizontal

    def check_collision_with_player(self, player):
        """Check if player has collected this medkit"""
        if not self.active:
            return False
        
        # Create collision rectangles
        medkit_rect = pygame.Rect(self.x, self.y, self.width, self.height)
        player_rect = pygame.Rect(player.x, player.y, player.width, player.height)
        return medkit_rect.colliderect(player_rect)

# Add function to spawn medkit
def spawn_medkit():
    while True:
        # Generate random position
        x = random.randint(0, WINDOW_WIDTH - 20)
        y = random.randint(0, WINDOW_HEIGHT - 20)
        
        # Check if position overlaps with obstacles
        valid_position = True
        medkit_rect = pygame.Rect(x, y, 20, 20)
        
        for obstacle in obstacles:
            obstacle_rect = pygame.Rect(obstacle.x, obstacle.y, obstacle.width, obstacle.height)
            if medkit_rect.colliderect(obstacle_rect):
                valid_position = False
                break
                
        if valid_position:
            return Medkit(x, y)

# Initialize Pygame's sound system
pygame.mixer.init()

# Sound loading with error handling
try:
    # Get the directory where the script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Build full paths to sound files
    paintball_sound_path = os.path.join(script_dir, "paintball_shot.wav") #AR-15 sound
    long_range_sound_path = os.path.join(script_dir, "long_range_sound.wav") #Sniper sound
    target_shot_path = os.path.join(script_dir, "target_shot.wav")
    game_over_path = os.path.join(script_dir, "game_over.wav")
    player_hit_path = os.path.join(script_dir, "player_hit.wav")
    
    # Debug information
    print(f"Attempting to load paintball sound from: {paintball_sound_path}")
    print(f"Attempting to load target shot sound from: {target_shot_path}")
    print(f"Attempting to load game over sound from: {game_over_path}")
    print(f"Attempting to load player hit sound from: {player_hit_path}")
    print(f"Attempting to load long range sound from: {long_range_sound_path}")

    # Load each sound file if it exists
    if os.path.exists(paintball_sound_path):
        paintball_sound = pygame.mixer.Sound(paintball_sound_path)
        paintball_sound.set_volume(0.9)  # 90% volume
        print("Successfully loaded paintball sound file")
    else:
        print(f"Error: Paintball sound file not found at {paintball_sound_path}")
        paintball_sound = None

    if os.path.exists(long_range_sound_path):
        long_range_sound = pygame.mixer.Sound(long_range_sound_path)
        long_range_sound.set_volume(0.9)  # 90% volume
        print("Successfully loaded long range sound file")
    else:
        print(f"Error: Long range sound file not found at {long_range_sound_path}")
        long_range_sound = None
        
    # Similar loading for target shot sound
    if os.path.exists(target_shot_path):
        target_shot_sound = pygame.mixer.Sound(target_shot_path)
        target_shot_sound.set_volume(0.7)  # 70% volume
        print("Successfully loaded target shot sound file")
    else:
        print(f"Error: Target shot sound file not found at {target_shot_path}")
        target_shot_sound = None
        
    # And game over sound
    if os.path.exists(game_over_path):
        game_over_sound = pygame.mixer.Sound(game_over_path)
        game_over_sound.set_volume(1.0)  # Full volume
        print("Successfully loaded game over sound file")
    else:
        print(f"Error: Game over sound file not found at {game_over_path}")
        game_over_sound = None

    # Load player hit sound
    if os.path.exists(player_hit_path):
        player_hit_sound = pygame.mixer.Sound(player_hit_path)
        player_hit_sound.set_volume(0.8)  # 80% volume
        print("Successfully loaded player hit sound file")
    else:
        print(f"Error: Player hit sound file not found at {player_hit_path}")
        player_hit_sound = None


except Exception as e:
    # If any error occurs during sound loading, disable all sounds
    print(f"Warning: Could not load sound effects. Error: {str(e)}")
    paintball_sound = None
    target_shot_sound = None
    game_over_sound = None

# Create game objects
player = Player()
targets = []
paintballs = []
bullets = []  # Add list for turret bullets
obstacles = []  # Add obstacles list
# Create num_targets random targets initially
num_targets = 3
NUM_OBSTACLES = 6
for _ in range(num_targets):
    targets.append(spawn_target(player))

# Create NUM_OBSTACLES random obstacles
for _ in range(NUM_OBSTACLES):
    while True:
        x = random.randint(0, WINDOW_WIDTH - 60)  # Account for obstacle width
        y = random.randint(0, WINDOW_HEIGHT - 60)  # Account for obstacle height
        
        # Check if obstacle overlaps with existing obstacles
        overlap = False
        for obstacle in obstacles:
            # Create rectangles for overlap check
            new_rect = pygame.Rect(x, y, 60, 60)
            existing_rect = pygame.Rect(obstacle.x, obstacle.y, obstacle.width, obstacle.height)
            if new_rect.colliderect(existing_rect):
                overlap = True
                break
        
        if not overlap:
            obstacles.append(Obstacle(x, y))
            break

# Add to game objects initialization
medkits = []  # Add after other game objects initialization
HEALTH_THRESHOLD = 20  # 20% health threshold for spawning medkit
MAX_HEALTH = 100

# Add near the top with other global variables
MAX_RANGE_PAINTBALL = min(WINDOW_WIDTH, WINDOW_HEIGHT) * 1
MAX_RANGE_BULLET = min(WINDOW_WIDTH, WINDOW_HEIGHT) * 1

# Medium range gun (AR-15) properties
MEDIUM_RANGE_DAMAGE = 50
MEDIUM_RANGE_DISTANCE = min(WINDOW_WIDTH, WINDOW_HEIGHT) * 0.8
MEDIUM_RANGE_FIRE_DELAY = 0.1
MEDIUM_RANGE_SPEED = 30  # Slower projectile speed

# Long range gun (Sniper) properties
LONG_RANGE_DAMAGE = 100
LONG_RANGE_DISTANCE = min(WINDOW_WIDTH, WINDOW_HEIGHT) * 2
LONG_RANGE_FIRE_DELAY = 0.5
LONG_RANGE_SPEED = 80  # Much faster projectile speed

# Game loop
running = True
clock = pygame.time.Clock()

# Add game state variables before game loop
game_over = False
grace_period = True
grace_period_start = time.time()
GRACE_PERIOD_DURATION = 5  # 5 seconds
font = pygame.font.Font(None, 64)
small_font = pygame.font.Font(None, 32)
score_font = pygame.font.Font(None, 36)  # Font for score display

# Add before game loop
fullscreen = False
previous_window_size = (WINDOW_WIDTH, WINDOW_HEIGHT)

# Add a variable to track if game over sound has been played
game_over_sound_played = False

while running:
    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_F11:  # Toggle fullscreen with F11
                fullscreen = not fullscreen
                if fullscreen:
                    previous_window_size = screen.get_size()
                    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
                else:
                    screen = pygame.display.set_mode(previous_window_size, pygame.RESIZABLE)
            elif event.key == pygame.K_ESCAPE and fullscreen:  # Exit fullscreen with ESC
                fullscreen = False
                screen = pygame.display.set_mode(previous_window_size, pygame.RESIZABLE)
            elif event.key == pygame.K_SPACE and game_over:
                # Reset player
                player = Player()
                # Reset targets
                targets = []
                for _ in range(num_targets):
                    targets.append(spawn_target(player))
                # Reset projectiles
                paintballs = []
                bullets = []
                # Reset obstacles
                obstacles = []
                for _ in range(NUM_OBSTACLES):
                    while True:
                        x = random.randint(0, WINDOW_WIDTH - 60)  # Account for obstacle width
                        y = random.randint(0, WINDOW_HEIGHT - 60)  # Account for obstacle height
                        overlap = False
                        for obs in obstacles:
                            # Create rectangles for overlap check
                            new_rect = pygame.Rect(x, y, 60, 60)
                            existing_rect = pygame.Rect(obs.x, obs.y, obs.width, obs.height)
                            if new_rect.colliderect(existing_rect):
                                overlap = True
                                break
                        if not overlap:
                            obstacles.append(Obstacle(x, y))
                            break
                # Reset game state
                game_over = False
                grace_period = True
                grace_period_start = time.time()
                game_over_sound_played = False  # Reset the sound played flag
                medkits = []  # Clear any existing medkits
            elif event.key == pygame.K_SPACE and not game_over:
                # Reset player
                player = Player()
                # Reset targets
                targets = []
                for _ in range(num_targets):
                    targets.append(spawn_target(player))
                # Reset projectiles
                paintballs = []
                bullets = []
                # Reset game state
                game_over = False
            elif event.key == pygame.K_1:  # Switch to medium range weapon
                player.current_weapon = "medium"
            elif event.key == pygame.K_2:  # Switch to long range weapon
                player.current_weapon = "long"
        elif event.type == pygame.VIDEORESIZE and not fullscreen:
            # Update window size
            WINDOW_WIDTH, WINDOW_HEIGHT = event.size
            screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
            # Update player position to stay in bounds if needed
            player.x = min(player.x, WINDOW_WIDTH - player.width)
            player.y = min(player.y, WINDOW_HEIGHT - player.height)

    if not game_over:
        # Check if grace period is over
        current_time = time.time()
        if grace_period and current_time - grace_period_start >= GRACE_PERIOD_DURATION:
            grace_period = False

        # Handle player movement
        keys = pygame.key.get_pressed()
        player.move(keys)

        # Handle shooting (only if grace period is over)
        if not grace_period and pygame.mouse.get_pressed()[0] and player.can_shoot():
            center_x = player.x + player.width // 2
            center_y = player.y + player.height // 2
            shot_angle = player.calculate_shot_angle()
            paintballs.append(Paintball(center_x, center_y, shot_angle, player.get_current_range(),
                                      speed=player.get_current_projectile_speed()))
            
            # Play sound effect
            current_weapon_sound = player.get_current_weapon_sound()
            if current_weapon_sound:
                current_weapon_sound.play()
                

        # Update paintballs
        for paintball in paintballs[:]:
            paintball.move()
            
            # Check for obstacle hits
            for obstacle in obstacles:
                if obstacle.check_collision(paintball.x, paintball.y, paintball.radius):
                    paintball.active = False
                    break
            
            if paintball.active:
                # Check for target hits
                for target in targets:
                    if not target.hit and paintball.check_hit(target):
                        target.health -= player.calculate_shot_damage()  # Use weapon-specific damage
                        paintball.active = False
                        
                        # Check if target is destroyed
                        if target.health <= 0:
                            target.hit = True
                            player.score += 1
                            targets.append(spawn_target(player))
                            targets.remove(target)
                        break
            
            # Remove inactive paintballs
            if not paintball.active:
                paintballs.remove(paintball)

        # Add target movement only if grace period is over
        if not grace_period:
            for target in targets:
                target.move_towards_player(player)

        # Update turret shooting only if grace period is over
        if not grace_period:
            current_time = time.time()
            for target in targets:
                if (not target.hit and 
                    target.can_shoot(current_time) and 
                    target.is_player_in_range(player)):  # Add range check
                    # Calculate start positions
                    bullet_start_x = target.x + target.width // 2
                    bullet_start_y = target.y + target.height // 2
                    player_center_x = player.x + player.width // 2
                    player_center_y = player.y + player.height // 2
                    
                    # Calculate angle with variance
                    shot_angle = target.calculate_shot_angle(player_center_x, player_center_y)
                    
                    # Create bullet with angle-based velocity
                    bullet = Bullet(bullet_start_x, bullet_start_y, 
                                 bullet_start_x + math.cos(shot_angle), 
                                 bullet_start_y + math.sin(shot_angle))
                    bullets.append(bullet)
                    
                    # Play target shot sound
                    if target_shot_sound:
                        target_shot_sound.play()

        # Update bullets
        for bullet in bullets[:]:
            bullet.move()
            
            # Check for obstacle hits
            for obstacle in obstacles:
                if obstacle.check_collision(bullet.x, bullet.y, bullet.radius):
                    bullet.active = False
                    break
            
            # Only check player collision if bullet is still active
            if bullet.active and bullet.check_hit_player(player):
                bullet.active = False
                player.health -= 10

                # Play player hit sound
                if player_hit_sound:
                    player_hit_sound.play()
                
                # Check if health is low and no medkits are active
                if player.health <= HEALTH_THRESHOLD and not medkits:
                    medkits.append(spawn_medkit())
                
                if player.health <= 0:
                    game_over = True
                    if game_over_sound and not game_over_sound_played:
                        game_over_sound.play()
                        game_over_sound_played = True
            
            # Remove inactive bullets
            if not bullet.active:
                bullets.remove(bullet)

        # Check for medkit collection
        for medkit in medkits[:]:
            if medkit.check_collision_with_player(player):
                player.health = MAX_HEALTH
                medkit.active = False
                medkits.remove(medkit)

        # Draw everything
        screen.fill(WHITE)
        
        # Draw obstacles
        for obstacle in obstacles:
            obstacle.draw(screen)
            
        # Draw medkits
        for medkit in medkits:
            medkit.draw(screen)
            
        player.draw(screen)
        
        # Draw targets
        for target in targets:
            target.draw(screen)
        
        # Draw paintballs
        for paintball in paintballs:
            paintball.draw(screen)

        # Draw bullets
        for bullet in bullets:
            bullet.draw(screen)

        # Draw score
        score_text = score_font.render(f"Score: {player.score}", True, BLACK)
        score_rect = score_text.get_rect(topright=(WINDOW_WIDTH - 10, 10))
        screen.blit(score_text, score_rect)

        # Draw grace period countdown and instructions if active
        if grace_period:
            time_left = max(0, GRACE_PERIOD_DURATION - (current_time - grace_period_start))
            grace_text = font.render(f"Grace Period: {int(time_left)}s", True, BLACK)
            grace_rect = grace_text.get_rect(center=(WINDOW_WIDTH/2, 50))
            screen.blit(grace_text, grace_rect)
            
            # Add weapon switch instructions
            instruction_text = small_font.render("Press '1' for AR-15, '2' for Sniper", True, BLACK)
            instruction_rect = instruction_text.get_rect(center=(WINDOW_WIDTH/2, 90))
            screen.blit(instruction_text, instruction_rect)

    else:
        # Draw game over message
        screen.fill(WHITE)
        game_over_text = font.render("GAME OVER", True, RED)
        score_text = small_font.render(f"Final Score: {player.score}", True, BLACK)
        restart_text = small_font.render("Press SPACE to restart", True, BLACK)
        
        text_rect = game_over_text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2 - 50))
        score_rect = score_text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2))
        restart_rect = restart_text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2 + 50))
        
        screen.blit(game_over_text, text_rect)
        screen.blit(score_text, score_rect)
        screen.blit(restart_text, restart_rect)

    # Update display
    pygame.display.flip()
    clock.tick(120)

pygame.quit()
