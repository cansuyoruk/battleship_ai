import random
from engine import Game
import numpy as np
import json

def play_game(ai1_type, ai2_type):
    """İki AI arasında bir oyun oynar ve sonuçları döndürür"""
    game = Game(human1=False, human2=False, ai_type=ai1_type, ai_type2=ai2_type)
    moves = 0
    hits = 0
    first_ai_hits = 0
    first_ai_shots = 0
    second_ai_hits = 0
    second_ai_shots = 0
    
    # Skor matrislerini sakla
    first_ai_scores = None
    second_ai_scores = None
    
    while not game.over:
        # Hamle öncesi skor matrisini kaydet
        if game.player1_turn:
            if ai1_type in ["greedy", "monte_carlo"]:
                first_ai_scores = game.get_ai_scores(1)  # Player 1'in skor matrisi
            first_ai_shots += 1
        else:
            if ai2_type in ["greedy", "monte_carlo"]:
                second_ai_scores = game.get_ai_scores(2)  # Player 2'nin skor matrisi
            second_ai_shots += 1
        
        game.ai_move()
        moves += 1
        
        # İsabet istatistiklerini kaydet
        if game.player1_turn:
            for i in range(100):
                if game.player2.search[i] == "H":
                    hits += 1
                    first_ai_hits += 1
        else:
            for i in range(100):
                if game.player1.search[i] == "H":
                    hits += 1
                    second_ai_hits += 1
    
    # Kazananı belirle
    winner = ai1_type if game.result == "1" else ai2_type
    
    return {
        'winner': winner,
        'moves': moves,
        'hits': hits,
        'first_ai_hits': first_ai_hits,
        'first_ai_shots': first_ai_shots,
        'second_ai_hits': second_ai_hits,
        'second_ai_shots': second_ai_shots,
        'first_ai_scores': first_ai_scores.tolist() if first_ai_scores is not None else None,
        'second_ai_scores': second_ai_scores.tolist() if second_ai_scores is not None else None
    }

def run_simulation():
    """Simülasyonu çalıştırır ve sonuçları kaydeder"""
    results = {}
    ai_types = ["random", "bfs", "monte_carlo", "greedy"]
    num_games = 100  # Her eşleşme için oynanacak oyun sayısı
    
    for ai1 in ai_types:
        for ai2 in ai_types:
            if ai1 < ai2:  # Aynı AI'ların kendisiyle eşleşmesini engelle
                match_key = f"{ai1} vs {ai2}"
                print(f"\nSimülasyon başlıyor: {match_key}")
                
                # Her eşleşme için num_games kadar oyun oyna
                wins = 0
                moves_list = []
                total_shots = 0
                hits = 0
                first_ai_hits = 0
                first_ai_shots = 0
                second_ai_hits = 0
                second_ai_shots = 0
                first_ai_score_sum = np.zeros((10, 10)) if ai1 in ["greedy", "monte_carlo"] else None
                second_ai_score_sum = np.zeros((10, 10)) if ai2 in ["greedy", "monte_carlo"] else None
                
                for game in range(num_games):
                    print(f"Oyun {game + 1}/{num_games}...")
                    game_result = play_game(ai1, ai2)
                    
                    if game_result['winner'] == ai1:
                        wins += 1
                    
                    moves_list.append(game_result['moves'])
                    total_shots += game_result['moves']
                    hits += game_result['hits']
                    first_ai_hits += game_result['first_ai_hits']
                    first_ai_shots += game_result['first_ai_shots']
                    second_ai_hits += game_result['second_ai_hits']
                    second_ai_shots += game_result['second_ai_shots']
                    
                    # Skor matrislerini topla
                    if game_result['first_ai_scores'] is not None:
                        first_ai_score_sum += np.array(game_result['first_ai_scores'])
                    if game_result['second_ai_scores'] is not None:
                        second_ai_score_sum += np.array(game_result['second_ai_scores'])
                
                # Sonuçları kaydet
                results[match_key] = {
                    'wins': wins,
                    'total_games': num_games,
                    'win_rate': (wins / num_games) * 100,
                    'avg_moves': sum(moves_list) / len(moves_list),
                    'move_counts': moves_list,
                    'total_shots': total_shots,
                    'hits': hits,
                    'accuracy': (hits / total_shots * 100) if total_shots > 0 else 0,
                    'first_ai_hits': first_ai_hits,
                    'first_ai_shots': first_ai_shots,
                    'first_ai_accuracy': (first_ai_hits / first_ai_shots * 100) if first_ai_shots > 0 else 0,
                    'second_ai_hits': second_ai_hits,
                    'second_ai_shots': second_ai_shots,
                    'second_ai_accuracy': (second_ai_hits / second_ai_shots * 100) if second_ai_shots > 0 else 0
                }
                
                # Skor matrislerini ortalama alarak kaydet
                if first_ai_score_sum is not None:
                    results[match_key]['first_ai_score_matrix'] = (first_ai_score_sum / num_games).tolist()
                if second_ai_score_sum is not None:
                    results[match_key]['second_ai_score_matrix'] = (second_ai_score_sum / num_games).tolist()
    
    # Sonuçları JSON dosyasına kaydet
    with open('simulation_results.json', 'w') as f:
        json.dump(results, f, indent=4)
    
    print("\nSimülasyon tamamlandı. Sonuçlar simulation_results.json dosyasına kaydedildi.")
    return results  # Sonuçları döndür

def save_results(results, filename='simulation_results.json'):
    """Simülasyon sonuçlarını JSON dosyasına kaydet"""
    # NumPy array'leri listeye çevir
    serializable_results = {}
    for match, data in results.items():
        serializable_results[match] = {
            k: v.tolist() if isinstance(v, np.ndarray) else v
            for k, v in data.items()
        }
    
    with open(filename, 'w') as f:
        json.dump(serializable_results, f, indent=4)
    print(f"\nSonuçlar {filename} dosyasına kaydedildi.")

def main():
    print("Simülasyon başlıyor...")
    results = run_simulation()  # Sonuçları al
    save_results(results)  # Sonuçları kaydet
    print("\nSimülasyon tamamlandı ve sonuçlar kaydedildi!")

if __name__ == "__main__":
    main() 