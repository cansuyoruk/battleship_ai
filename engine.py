import random
import numpy as np
import matplotlib.pyplot as plt

# Matplotlib ayarları
plt.ion()  # Interactive modu aç

class Ship:
    def __init__(self, size):
        self.size = size
        self.row = random.randint(0, 9)
        self.col = random.randint(0, 9)
        self.orientation = random.choice(["h", "v"])
        self.hits = 0
        self.indexes = self.compute_indexes()

    def compute_indexes(self):
        indexes = []
        for i in range(self.size):
            r = self.row + (i if self.orientation == "v" else 0)
            c = self.col + (i if self.orientation == "h" else 0)
            if r >= 10 or c >= 10:
                return []
            indexes.append(r * 10 + c)
        return indexes

    def contains(self, row, col):
        return (row * 10 + col) in self.indexes


class Player:
    def __init__(self):
        self.ships = []
        self.search = ["U" for _ in range(100)]
        self.opponent_board = ["U" for _ in range(100)]
        self.place_ships()

    def place_ships(self, sizes=[5, 4, 3, 3, 2]):
        for size in sizes:
            while True:
                ship = Ship(size)
                if ship.indexes and not any(i in sum([s.indexes for s in self.ships], []) for i in ship.indexes):
                    self.ships.append(ship)
                    break


class Game:
    def __init__(self, human1=True, human2=True, ai_type="random", ai_type2="random"):
        self.player1 = Player()
        self.player2 = Player()
        self.human1 = human1
        self.human2 = human2
        self.player1_turn = True
        self.over = False
        self.result = None
        self.ai_type = ai_type
        self.ai_type2 = ai_type2

    def make_move(self, row, col):
        if self.over:
            return False

        current_player = self.player1 if self.player1_turn else self.player2
        target_player = self.player2 if self.player1_turn else self.player1
        index = row * 10 + col

        if current_player.search[index] != "U":
            return False

        hit = False
        for ship in target_player.ships:
            if ship.contains(row, col):
                hit = True
                current_player.search[index] = "H"
                target_player.opponent_board[index] = "H"
                ship.hits += 1
                if ship.hits == ship.size:
                    self.mark_sunken_ship(ship, current_player, target_player)
                break

        if not hit:
            current_player.search[index] = "M"
            target_player.opponent_board[index] = "M"

        if self.check_game_over():
            self.over = True
            self.result = "1" if self.player1_turn else "2"
        else:
            self.player1_turn = not self.player1_turn

        return True

    def mark_sunken_ship(self, ship, current_player, target_player):
        for i in range(ship.size):
            r = ship.row + (i if ship.orientation == "v" else 0)
            c = ship.col + (i if ship.orientation == "h" else 0)
            idx = r * 10 + c
            current_player.search[idx] = "S"
            target_player.opponent_board[idx] = "S"

    def check_game_over(self):
        target_player = self.player2 if self.player1_turn else self.player1
        return all(ship.hits == ship.size for ship in target_player.ships)

    def ai_move(self):
        if self.over:
            return False

        ai_type = self.ai_type if self.player1_turn else self.ai_type2
        if ai_type == "random":
            move = self.random_ai()
        elif ai_type == "bfs":
            move = self.bfs_ai()

        elif ai_type == "monte_carlo":
            move = self.monte_carlo_ai()
        elif ai_type == "greedy":
            move = self.greedy_ai()
        else:
            move = self.random_ai()

        return self.make_move(*move)

    def get_hits(self, player):
        return [(i // 10, i % 10) for i, val in enumerate(player.search) if val == "H"]

    def get_neighbors(self, row, col):
        return [(r, c) for r, c in [(row-1,col), (row+1,col), (row,col-1), (row,col+1)] if 0 <= r < 10 and 0 <= c < 10]

    def random_ai(self):
        current = self.player1 if self.player1_turn else self.player2
        search = current.search
        choices = [(i // 10, i % 10) for i, val in enumerate(search) if val == "U"]
        return random.choice(choices) if choices else (0, 0)

    def bfs_ai(self):
        current = self.player1 if self.player1_turn else self.player2
        search = current.search
        hits = self.get_hits(current)
        
        # Vurulan karelerin etrafını ara
        if hits:
            for row, col in hits:
                for r, c in self.get_neighbors(row, col):
                    if search[r * 10 + c] == "U":
                        return r, c
        
        # Vurulan kare yoksa, merkeze yakın kareleri ara
        center_squares = [(i,j) for i in range(3,7) for j in range(3,7)
                         if search[i * 10 + j] == "U"]
        if center_squares:
            return random.choice(center_squares)
        
        # Merkezde kare kalmadıysa, rastgele bir kare seç
        available_moves = [(i // 10, i % 10) for i, val in enumerate(search) if val == "U"]
        if available_moves:
            return random.choice(available_moves)
        
        # Eğer hiç kare kalmadıysa, ilk boş kareyi seç
        for i in range(100):
            if search[i] == "U":
                return i // 10, i % 10

    def evaluate_position(self, row, col):
        current = self.player1 if self.player1_turn else self.player2
        search = current.search
        score = 0
        for r, c in self.get_neighbors(row, col):
            val = search[r * 10 + c]
            if val == "H":
                score += 2
            elif val == "M":
                score -= 1
        center_dist = abs(row - 4.5) + abs(col - 4.5)
        score += (9 - center_dist) / 2
        return score

    def generate_simple_board(self, known_board, ship_sizes):
        """Basitleştirilmiş gemi yerleştirme stratejisi"""
        board = [0 for _ in range(100)]
        max_attempts = 1000  # Maksimum deneme sayısını artırdık

        # Vurulan kareleri bul
        hit_squares = [(i // 10, i % 10) for i, val in enumerate(known_board) if val == "H"]
        
        # Vurulan kareleri kapsayan gemileri yerleştir
        for hit in hit_squares:
            hit_covered = False
            for size in ship_sizes[:]:  # Liste kopyası kullan
                if hit_covered:
                    break
                    
                # Yatay ve dikey yerleşimleri dene
                for orientation in ["h", "v"]:
                    if hit_covered:
                        break
                        
                    # Gemi başlangıç pozisyonunu hesapla
                    if orientation == "h":
                        start_col = max(0, hit[1] - size + 1)
                        start_row = hit[0]
                    else:
                        start_row = max(0, hit[0] - size + 1)
                        start_col = hit[1]
                    
                    # Gemi yerleştirme kontrolü
                    valid = True
                    indexes = []
                    
                    for i in range(size):
                        r = start_row + (i if orientation == "v" else 0)
                        c = start_col + (i if orientation == "h" else 0)
                        
                        if r >= 10 or c >= 10:
                            valid = False
                            break
                            
                        idx = r * 10 + c
                        if known_board[idx] in ["M", "S"] or board[idx] == 1:
                            valid = False
                            break
                            
                        indexes.append((r, c))
                    
                    if valid and hit in indexes:
                        for r, c in indexes:
                            board[r * 10 + c] = 1
                        hit_covered = True
                        ship_sizes.remove(size)
                        break

        # Kalan gemileri yerleştir
        remaining_ships = ship_sizes.copy()
        for size in remaining_ships:
            placed = False
            attempts = 0
            
            while not placed and attempts < max_attempts:
                attempts += 1
                row = random.randint(0, 9)
                col = random.randint(0, 9)
                orientation = random.choice(["h", "v"])
                
                valid = True
                indexes = []
                
                for i in range(size):
                    r = row + (i if orientation == "v" else 0)
                    c = col + (i if orientation == "h" else 0)
                    
                    if r >= 10 or c >= 10:
                        valid = False
                        break
                        
                    idx = r * 10 + c
                    if known_board[idx] in ["M", "S"] or board[idx] == 1:
                        valid = False
                        break
                        
                    indexes.append((r, c))
                
                if valid:
                    for r, c in indexes:
                        board[r * 10 + c] = 1
                    placed = True
                    ship_sizes.remove(size)

        return board

    def create_heatmap(self, score_board, known_board):
        """Creates a heatmap visualization of the Monte Carlo simulation results"""
        import matplotlib.pyplot as plt
        import numpy as np
        
        # Convert scores to 10x10 matrix
        heatmap_data = np.array(score_board).reshape(10, 10)
        mask = np.array(known_board).reshape(10, 10) != "U"
        
        # Normalize data between 0-1
        if heatmap_data.max() > heatmap_data.min():
            heatmap_data = (heatmap_data - heatmap_data.min()) / (heatmap_data.max() - heatmap_data.min())
        
        # Create new figure with white background
        plt.figure(figsize=(8, 8), facecolor='white')
        
        # Draw heatmap
        plt.imshow(heatmap_data, cmap='YlOrRd', interpolation='nearest')
        
        # Mark hit squares
        for i in range(10):
            for j in range(10):
                if known_board[i * 10 + j] == "H":
                    plt.plot(j, i, 'go', markersize=12, label='Hit')  # Green circle
                elif known_board[i * 10 + j] == "M":
                    plt.plot(j, i, 'kx', markersize=10, label='Miss')  # Black X
                elif known_board[i * 10 + j] == "S":
                    plt.plot(j, i, 'rs', markersize=10, label='Sunk')  # Red square
        
        # Add colorbar
        cbar = plt.colorbar(label='Ship Probability')
        cbar.ax.set_ylabel('Ship Probability', color='black')
        
        # Add grid
        plt.grid(True, which='major', color='black', linestyle='-', linewidth=0.5)
        plt.xticks(range(10), color='black')
        plt.yticks(range(10), color='black')
        
        # Set title and labels
        plt.title('Monte Carlo AI Prediction Map', color='black', pad=20)
        plt.xlabel('○: Hit | ×: Miss | □: Sunk', color='black')
        
        # Remove duplicate legend entries
        handles, labels = plt.gca().get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        plt.legend(by_label.values(), by_label.keys(), 
                  loc='center left', bbox_to_anchor=(1, 0.5))
        
        # Adjust layout to prevent cutting off
        plt.tight_layout()
        
        # Save and close
        plt.savefig('monte_carlo_heatmap.png', 
                   bbox_inches='tight', 
                   facecolor='white',
                   edgecolor='none',
                   pad_inches=0.1)
        plt.close()
        
        return heatmap_data

    def greedy_ai(self):
        current = self.player1 if self.player1_turn else self.player2
        search = current.search
        best_score = -float("inf")
        best_move = (0, 0)

        for i in range(100):
            if search[i] == "U":
                row, col = i // 10, i % 10
                score = 0

                for r, c in self.get_neighbors(row, col):
                    val = search[r * 10 + c]
                    if val == "H":
                        score += 3
                    elif val == "M":
                        score -= 2

                center_dist = abs(row - 4.5) + abs(col - 4.5)
                score += (9 - center_dist) / 2

                if (row + col) % 2 == 0:
                    score += 0.5

                if score > best_score:
                    best_score = score
                    best_move = (row, col)

        return best_move

    def monte_carlo_ai(self):
        current = self.player1 if self.player1_turn else self.player2
        search = current.search
        hits = self.get_hits(current)
        
        # 1. Vurulan karenin etrafını ara (BFS benzeri strateji)
        if hits:
            for row, col in hits:
                for r, c in self.get_neighbors(row, col):
                    if search[r * 10 + c] == "U":
                        return r, c
        
        # 2. Monte Carlo simülasyonu için skor tablosu
        score_board = np.zeros((10, 10))
        
        # Vurulan, ıskalanan ve batık kareleri -1 yap
        for i in range(100):
            if search[i] != "U":
                score_board[i // 10][i % 10] = -1
        
        # 3. Daha fazla simülasyon yap

        num_simulations = 100  # Simülasyon sayısını artırdık
        
        for _ in range(num_simulations):
            # Basit gemi yerleşimi oluştur
            temp_board = self.generate_simple_board(search, [5, 4, 3, 3, 2])
            
            # Skor tablosunu güncelle
            for i in range(100):
                if temp_board[i] == 1 and score_board[i // 10][i % 10] != -1:
                    score_board[i // 10][i % 10] += 1
        
        # 4. Vurulan karelerin etrafına daha yüksek bonus puan ver
        for row, col in hits:
            for r, c in self.get_neighbors(row, col):
                if 0 <= r < 10 and 0 <= c < 10 and score_board[r][c] != -1:
                    score_board[r][c] += 20  # Bonus puanı artırdık
        
        # 5. Merkeze yakın karelere daha yüksek bonus puan ver
        for i in range(10):
            for j in range(10):
                if score_board[i][j] != -1:
                    center_dist = abs(i - 4.5) + abs(j - 4.5)
                    score_board[i][j] += (9 - center_dist) * 3  # Merkez bonusunu artırdık
        
        # 6. Vurulan karelerin etrafındaki karelerin etrafına da bonus puan ver
        for row, col in hits:
            for r, c in self.get_neighbors(row, col):
                if 0 <= r < 10 and 0 <= c < 10 and score_board[r][c] != -1:
                    for r2, c2 in self.get_neighbors(r, c):
                        if 0 <= r2 < 10 and 0 <= c2 < 10 and score_board[r2][c2] != -1:
                            score_board[r2][c2] += 10  # Bonus puanı artırdık
        
        # 7. Heatmap'i göster
        self.create_heatmap(score_board.flatten(), search)
        
        # 8. En yüksek skorlu hücreyi seç
        max_score = -1
        best_move = None
        
        for i in range(10):
            for j in range(10):
                if score_board[i][j] > max_score:
                    max_score = score_board[i][j]
                    best_move = (i,j)
        
        # 9. Eğer en iyi hamle bulunamadıysa, merkeze yakın bir kare seç
        if best_move is None:
            center_squares = [(i,j) for i in range(3,7) for j in range(3,7)
                            if search[i * 10 + j] == "U"]
            if center_squares:
                best_move = random.choice(center_squares)
            else:
                available_moves = [(i // 10, i % 10) for i, val in enumerate(search) if val == "U"]
                if available_moves:
                    best_move = random.choice(available_moves)
        
        return best_move

    def get_ai_scores(self, player_num):
        """Belirtilen oyuncu için skor matrisini hesaplar ve döndürür"""
        if player_num == 1:
            current = self.player1
            ai_type = self.ai_type
        else:
            current = self.player2
            ai_type = self.ai_type2
            
        search = current.search
        scores = np.zeros((10, 10))
        
        if ai_type == "greedy":
            # Greedy AI için skor hesaplama
            for i in range(10):
                for j in range(10):
                    if search[i * 10 + j] == "U":
                        score = 0
                        # Komşu kareleri kontrol et
                        for r, c in self.get_neighbors(i, j):
                            val = search[r * 10 + c]
                            if val == "H":
                                score += 3
                            elif val == "M":
                                score -= 2
                        
                        # Merkeze yakınlık bonusu
                        center_dist = abs(i - 4.5) + abs(j - 4.5)
                        score += (9 - center_dist) / 2
                        
                        # Çapraz kare bonusu
                        if (i + j) % 2 == 0:
                            score += 0.5
                            
                        scores[i][j] = score
                    else:
                        scores[i][j] = -1
                        
        elif ai_type == "monte_carlo":
            # Monte Carlo AI için skor hesaplama
            hits = self.get_hits(current)
            
            # Monte Carlo simülasyonları
            num_simulations = 100
            for _ in range(num_simulations):
                temp_board = self.generate_simple_board(search, [5, 4, 3, 3, 2])
                for i in range(100):
                    if temp_board[i] == 1 and search[i] == "U":
                        scores[i // 10][i % 10] += 1
            
            # Vurulan karelerin etrafına bonus
            for row, col in hits:
                for r, c in self.get_neighbors(row, col):
                    if 0 <= r < 10 and 0 <= c < 10 and search[r * 10 + c] == "U":
                        scores[r][c] += 20
            
            # Merkez bonusu
            for i in range(10):
                for j in range(10):
                    if search[i * 10 + j] == "U":
                        center_dist = abs(i - 4.5) + abs(j - 4.5)
                        scores[i][j] += (9 - center_dist) * 3
            
            # Vurulan karelerin çevresine bonus
            for row, col in hits:
                for r, c in self.get_neighbors(row, col):
                    if 0 <= r < 10 and 0 <= c < 10 and search[r * 10 + c] == "U":
                        for r2, c2 in self.get_neighbors(r, c):
                            if 0 <= r2 < 10 and 0 <= c2 < 10 and search[r2 * 10 + c2] == "U":
                                scores[r2][c2] += 10
        
        return scores