import pygame
import sys
import csv
import time
import matplotlib.pyplot as plt

pygame.init()

# Dimensions de la fenêtre
WIDTH, HEIGHT = 1280,720
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Piano pour débutants - Frère Jacques")

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
GREENER = (35, 150, 35)
RED = (255, 0, 0)

class Player:
    def __init__(self, name):
        self.name = name
        self.score = 0
        self.streak = 0
        self.reaction_times = []

class PianoKey:
    def __init__(self, x, y, width, height, note, key_bind, is_black=False):
        self.rect = pygame.Rect(x, y, width, height)
        self.note = note
        self.key_bind = key_bind
        self.is_black = is_black
        self.default_color = WHITE if not is_black else BLACK
        self.color = self.default_color
        self.highlight_end_time = None  
        self.highlight_color = None  

    def draw(self, surface):
        # Vérifier si le temps de surlignage est écoulé
        if self.highlight_end_time is not None:
            if pygame.time.get_ticks() >= self.highlight_end_time:
                self.reset_color()
        pygame.draw.rect(surface, self.color, self.rect)
        pygame.draw.rect(surface, BLACK, self.rect, 1)  # Bordure

    def highlight(self, color, duration):
        self.highlight_color = color
        self.highlight_end_time = pygame.time.get_ticks() + duration
        self.color = color

    def reset_color(self):
        self.color = self.default_color
        self.highlight_end_time = None
        self.highlight_color = None

def create_piano_keys():
    keys = []
    key_width = WIDTH // 7
    key_height = HEIGHT // 2
    notes = ['do', 're', 'mi', 'fa', 'sol', 'la', 'si']
    key_binds = [pygame.K_a, pygame.K_z, pygame.K_e, pygame.K_r, pygame.K_t, pygame.K_y, pygame.K_u]
    
    for i in range(7):
        x = i * key_width
        y = HEIGHT // 2
        key = PianoKey(x, y, key_width, key_height, notes[i], key_binds[i])
        keys.append(key)
    
    # Ajout des touches noires pour le visuel (ne sont pas interactives)
    black_keys = []
    black_key_width = key_width // 2
    black_key_height = key_height // 2
    black_key_positions = [0.75, 1.75, 3.75, 4.75, 5.75]  
    
    for pos in black_key_positions:
        x = int(pos * key_width)
        y = HEIGHT // 2
        key = PianoKey(x, y, black_key_width, black_key_height, None, None, is_black=True)
        black_keys.append(key)
    
    return keys + black_keys

def load_sounds():
    sounds = {}
    notes = ['do', 're', 'mi', 'fa', 'sol', 'la', 'si']
    for note in notes:
        sounds[note] = pygame.mixer.Sound(f"{note}.wav")
    return sounds

class Leaderboard:
    def __init__(self):
        self.filename = 'leaderboard.csv'
        self.data = self.load_data()

    def load_data(self):
        data = []
        try:
            with open(self.filename, 'r', newline='') as file:
                reader = csv.DictReader(file, fieldnames=['name', 'score', 'streak', 'reaction_time'])
                for row in reader:
                    data.append(row)
            # Supprimer la ligne d en-tête 
            if data and data[0]['name'] == 'name':
                data = data[1:]
        except FileNotFoundError:
            pass
        return data

    def get_top_scores(self):
        sorted_data = sorted(self.data, key=lambda x: int(x['score']), reverse=True)
        return sorted_data[:3]

class GraphManager:
    def __init__(self, player_name):
        self.player_name = player_name
        self.leaderboard = Leaderboard()

    def create_graphs(self):
        player_games = [row for row in self.leaderboard.data if row['name'] == self.player_name]
        if not player_games:
            print("Aucune donné pour ce joueur.")
            return

        # Temps de réaction moyen par partie
        reaction_times = [float(row['reaction_time']) for row in player_games]
        plt.figure()
        plt.plot(range(1, len(reaction_times) + 1), reaction_times, marker='o')
        plt.title("Temps de réaction moyen par partie")
        plt.xlabel("Partie")
        plt.ylabel("Temps de réaction (s)")
        plt.savefig("reaction_times.png")

        # Score final par partie
        scores = [int(row['score']) for row in player_games]
        plt.figure()
        plt.plot(range(1, len(scores) + 1), scores, marker='o', color='green')
        plt.title("Score final par partie")
        plt.xlabel("Partie")
        plt.ylabel("Score")
        plt.savefig("scores.png")

        # Score moyen par joueur
        players = {}
        for row in self.leaderboard.data:
            name = row['name']
            score = int(row['score'])
            if name in players:
                players[name]['total_score'] += score
                players[name]['games_played'] += 1
            else:
                players[name] = {'total_score': score, 'games_played': 1}
        avg_scores = {name: data['total_score'] / data['games_played'] for name, data in players.items()}

        plt.figure()
        plt.bar(avg_scores.keys(), avg_scores.values(), color='orange')
        plt.title("Score moyen par joueur")
        plt.xlabel("Joueur")
        plt.ylabel("Score moyen")
        plt.savefig("average_scores.png")

        # Affichage des images 
        print("Graphiques générés: reaction_times.png, scores.png, average_scores.png")

class Game:
    def __init__(self):
        self.keys = create_piano_keys()
        self.sounds = load_sounds()
        self.player = None
        self.running = True
        self.paused = False
        self.current_note_index = 0
        # Notes de "Frère Jacques"
        self.song_notes = [
            'do', 're', 'mi', 'do',
            'do', 're', 'mi', 'do',
            'mi', 'fa', 'sol',
            'mi', 'fa', 'sol',
            'sol', 'la', 'sol', 'fa', 'mi', 'do',
            'sol', 'la', 'sol', 'fa', 'mi', 'do',
            'do', 'sol', 'do',
            'do', 'sol', 'do'
        ]
        self.note_timing = 800  # Temps en ms entre les notes
        self.last_note_time = pygame.time.get_ticks()
        self.score = 0
        self.streak = 0
        self.reaction_times = []
        self.note_active = False
        self.active_key = None
        self.game_start_time = time.time()
        self.pause_text = None

    def start(self):
        self.show_menu()

    def get_player_name(self):
        name = ""
        entering_name = True
        font = pygame.font.Font(None, 50)
        while entering_name:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    entering_name = False
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        entering_name = False
                    elif event.key == pygame.K_BACKSPACE:
                        name = name[:-1]
                    else:
                        name += event.unicode

            WINDOW.fill(BLACK)
            prompt_text = font.render("Entrez votre nom:", True, WHITE)
            name_text = font.render(name, True, WHITE)
            WINDOW.blit(prompt_text, (WIDTH // 2 - prompt_text.get_width() // 2, HEIGHT // 3))
            WINDOW.blit(name_text, (WIDTH // 2 - name_text.get_width() // 2, HEIGHT // 2))
            pygame.display.flip()
        return name

    def show_menu(self):
        while True:
            WINDOW.fill(BLACK)
            font = pygame.font.Font(None, 74)
            title_text = font.render("Jeu de Piano", True, WHITE)
            WINDOW.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 4))

            font = pygame.font.Font(None, 50)
            new_game_text = font.render("Nouvelle Partie (N)", True, WHITE)
            leaderboard_text = font.render("Leaderboard (L)", True, WHITE)

            WINDOW.blit(new_game_text, (WIDTH // 2 - new_game_text.get_width() // 2, HEIGHT // 2))
            WINDOW.blit(leaderboard_text, (WIDTH // 2 - leaderboard_text.get_width() // 2, HEIGHT // 2 + 60))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_n:
                        player_name = self.get_player_name()
                        self.player = Player(player_name)
                        self.main_loop()
                        return
                    elif event.key == pygame.K_l:
                        self.display_leaderboard()
                        return

    def display_leaderboard(self):
        leaderboard = Leaderboard()
        top_scores = leaderboard.get_top_scores()

        while True:
            WINDOW.fill(BLACK)
            font = pygame.font.Font(None, 74)
            title_text = font.render("Leaderboard", True, WHITE)
            WINDOW.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 8))

            font = pygame.font.Font(None, 50)
            for i, entry in enumerate(top_scores):
                score_text = font.render(f"{i+1}. {entry['name']} - {entry['score']}", True, WHITE)
                WINDOW.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 4 + i * 60))

            back_text = font.render("Appuyez sur B pour revenir", True, WHITE)
            WINDOW.blit(back_text, (WIDTH // 2 - back_text.get_width() // 2, HEIGHT - 100))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_b:
                        self.show_menu()
                        return

    def main_loop(self):
        self.running = True  
        self.current_note_index = 0  # Réinitialiser l'index de la chanson
        self.last_note_time = pygame.time.get_ticks()  # Réinitialiser le temps
        self.score = 0  # Réinitialiser le score
        self.streak = 0  # Réinitialiser le streak
        self.reaction_times = []  # Réinitialiser les temps de reaction
        self.note_active = False
        self.active_key = None

        while self.running:
            self.handle_events()
            if not self.paused:
                self.update()
                self.draw()
            else:
                self.display_pause_screen()
            pygame.display.flip()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                else:
                    self.check_key_press(event.key)

    def update(self):
        current_time = pygame.time.get_ticks()
        if not self.note_active and current_time - self.last_note_time >= self.note_timing:
            # Activer la prochaine note
            if self.current_note_index < len(self.song_notes):
                note = self.song_notes[self.current_note_index]
                self.activate_note(note)
                self.current_note_index += 1
                self.last_note_time = current_time
            else:
                # Fin de la chanson
                self.end_game()

        # Vérifier si le joueur a manqué la note
        if self.note_active and (current_time - self.last_note_time >= 800):
            # Note manquée
            self.active_key.highlight(RED, 300)  
            self.note_active = False
            self.active_key = None
            self.streak = 0
            self.last_note_time = current_time

    def draw(self):
        WINDOW.fill(BLACK)
        for key in self.keys:
            key.draw(WINDOW)
        # Afficher les informations du joueur
        self.display_player_info()

    def activate_note(self, note):
        for key in self.keys:
            if key.note == note:
                key.highlight(GREEN, 800)  # La touche est surlignée en vert pour indiquer qu'il faut appuyer
                self.note_active = True
                self.active_key = key
                self.note_activation_time = time.time()
                break

    def check_key_press(self, key_pressed):
        for key in self.keys:
            if key.key_bind == key_pressed:
                if key.note:
                    self.sounds[key.note].play()
                if self.note_active and key == self.active_key:
                    # Bonne note jouée
                    reaction_time = time.time() - self.note_activation_time
                    self.reaction_times.append(reaction_time)
                    self.score += 10
                    self.streak += 1
                    # La touche devient vert doncé pendant 0.5s à partir du moment où le joueur appuie
                    self.active_key.highlight(GREENER, 300)
                    self.note_active = False
                    self.active_key = None
                    self.last_note_time = pygame.time.get_ticks()
                else:
                    # Mauvaise note
                    self.streak = 0

    def end_game(self):
        self.running = False
        self.save_player_data()
        self.display_leaderboard_and_graphs()

    def save_player_data(self):
        avg_reaction_time = sum(self.reaction_times) / len(self.reaction_times) if self.reaction_times else 0
        with open('leaderboard.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([self.player.name, self.score, self.streak, avg_reaction_time])

    def display_player_info(self):
        font = pygame.font.Font(None, 36)
        # Nom du joueur
        name_text = font.render(f"Joueur: {self.player.name}", True, WHITE)
        WINDOW.blit(name_text, (10, 10))
        # Score
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        WINDOW.blit(score_text, (10, 50))
        # Temps de réaction moyen
        avg_reaction_time = sum(self.reaction_times) / len(self.reaction_times) if self.reaction_times else 0
        reaction_text = font.render(f"Temps de réaction moyen: {avg_reaction_time:.2f}s", True, WHITE)
        WINDOW.blit(reaction_text, (10, 90))
        # Streak
        streak_text = font.render(f"Streak: {self.streak}", True, WHITE)
        WINDOW.blit(streak_text, (10, 130))

    def display_leaderboard_and_graphs(self):
        # Afficher le leaderboard et les graphiques
        WINDOW.fill(BLACK)
        leaderboard = Leaderboard()
        top_scores = leaderboard.get_top_scores()

        font = pygame.font.Font(None, 74)
        title_text = font.render("Fin de la partie", True, WHITE)
        WINDOW.blit(title_text, (WIDTH // 2 - title_text.get_width() // 2, HEIGHT // 8))

        font = pygame.font.Font(None, 50)
        for i, entry in enumerate(top_scores):
            score_text = font.render(f"{i+1}. {entry['name']} - {entry['score']}", True, WHITE)
            WINDOW.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 4 + i * 60))

        pygame.display.flip()
        pygame.time.wait(3000)

        # Générer les graphiques
        graph_manager = GraphManager(self.player.name)
        graph_manager.create_graphs()

        # Affichage des graphiques
        self.display_graphs()

    def display_graphs(self):
        # Charger les images des graphiques
        reaction_image = pygame.image.load("reaction_times.png")
        scores_image = pygame.image.load("scores.png")
        average_scores_image = pygame.image.load("average_scores.png")

        # Redimensionner les images pour tenir sur l'écran
        reaction_image = pygame.transform.scale(reaction_image, (WIDTH // 3, HEIGHT // 2))
        scores_image = pygame.transform.scale(scores_image, (WIDTH // 3, HEIGHT // 2))
        average_scores_image = pygame.transform.scale(average_scores_image, (WIDTH // 3, HEIGHT // 2))

        # Afficher les images
        WINDOW.fill(BLACK)
        WINDOW.blit(reaction_image, (0, HEIGHT // 2))
        WINDOW.blit(scores_image, (WIDTH // 3, HEIGHT // 2))
        WINDOW.blit(average_scores_image, (2 * WIDTH // 3, HEIGHT // 2))

        pygame.display.flip()
        # Attend que le joueur appuie sur unetouche pour revenir au meni
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    waiting = False
        self.show_menu()

    def display_pause_screen(self):
        font = pygame.font.Font(None, 74)
        pause_text = font.render("Pause", True, WHITE)
        WINDOW.blit(pause_text, (WIDTH // 2 - pause_text.get_width() // 2, HEIGHT // 2 - pause_text.get_height() // 2))

if __name__ == "__main__":
    game = Game()
    game.start()
