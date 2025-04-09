import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import json
from scipy import stats
import os
from matplotlib.patches import Circle, RegularPolygon
from matplotlib.path import Path
from matplotlib.projections.polar import PolarAxes
from matplotlib.projections import register_projection
from matplotlib.spines import Spine
from matplotlib.transforms import Affine2D
import pandas as pd
from sklearn.tree import DecisionTreeClassifier, plot_tree
from sklearn.preprocessing import LabelEncoder
import networkx as nx

def load_results(filename='simulation_results.json'):
    """JSON dosyasından simülasyon sonuçlarını yükle"""
    with open(filename, 'r') as f:
        results = json.load(f)
    
    # Liste olan değerleri NumPy array'e çevir
    for match in results:
        if 'move_counts' in results[match]:
            results[match]['move_counts'] = np.array(results[match]['move_counts'])
    
    return results

def set_style():
    """Grafik stilini ayarla"""
    # Profesyonel renk paleti
    colors = ['#2ecc71', '#3498db', '#e74c3c', '#f1c40f', '#9b59b6', '#1abc9c']
    
    # Seaborn stil ayarları
    sns.set_style("whitegrid")
    sns.set_context("notebook", font_scale=1.2)
    
    # Matplotlib stil ayarları
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.grid'] = True
    plt.rcParams['grid.alpha'] = 0.3
    plt.rcParams['grid.linestyle'] = '--'
    plt.rcParams['axes.edgecolor'] = '#2c3e50'
    plt.rcParams['axes.linewidth'] = 1.0
    plt.rcParams['xtick.color'] = '#2c3e50'
    plt.rcParams['ytick.color'] = '#2c3e50'
    plt.rcParams['text.color'] = '#2c3e50'
    plt.rcParams['axes.labelcolor'] = '#2c3e50'
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.facecolor'] = 'white'
    
    return colors

def analyze_win_stats(results):
    """Analyzes and visualizes win rates between AIs"""
    plt.figure(figsize=(15, 8))
    
    # Calculate total win rate for each AI
    ai_win_rates = {}
    for match, data in results.items():
        ai1, ai2 = match.split(" vs ")
        if ai1 not in ai_win_rates:
            ai_win_rates[ai1] = []
        if ai2 not in ai_win_rates:
            ai_win_rates[ai2] = []
        
        ai_win_rates[ai1].append(data['win_rate'])
        ai_win_rates[ai2].append(100 - data['win_rate'])
    
    # Calculate average win rate for each AI
    avg_win_rates = {ai: np.mean(rates) for ai, rates in ai_win_rates.items()}
    
    # Create bar plot
    plt.bar(avg_win_rates.keys(), avg_win_rates.values())
    plt.title('Figure 1: AI Win Rates')
    plt.xlabel('AI Type')
    plt.ylabel('Average Win Rate (%)')
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    
    # Show values on top of bars
    for i, v in enumerate(avg_win_rates.values()):
        plt.text(i, v + 1, f'{v:.1f}%', ha='center')
    
    plt.savefig('figures/win_stats.png')
    plt.close()

def analyze_accuracy(results):
    """Analyzes and visualizes hit rates"""
    plt.figure(figsize=(15, 8))
    
    matches = []
    first_ai_accuracies = []
    second_ai_accuracies = []
    
    for match, data in results.items():
        matches.append(match)
        first_ai_accuracies.append(data['first_ai_accuracy'])
        second_ai_accuracies.append(data['second_ai_accuracy'])
    
    x = np.arange(len(matches))
    width = 0.35
    
    plt.bar(x - width/2, first_ai_accuracies, width, label='First AI')
    plt.bar(x + width/2, second_ai_accuracies, width, label='Second AI')
    
    plt.title('Figure 2: AI Hit Rates')
    plt.xlabel('Matches')
    plt.ylabel('Hit Rate (%)')
    plt.xticks(x, matches, rotation=45, ha='right')
    plt.legend()
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig('figures/hit_rates.png')
    plt.close()

def analyze_moves(results):
    """Analyzes and visualizes move count distribution"""
    plt.figure(figsize=(15, 8))
    
    matches = []
    move_data = []
    
    for match, data in results.items():
        matches.append(match)
        move_data.append(data['move_counts'])
    
    plt.boxplot(move_data, tick_labels=matches)
    plt.title('Figure 3: Move Count Distribution')
    plt.xlabel('Matches')
    plt.ylabel('Number of Moves')
    plt.xticks(rotation=45, ha='right')
    plt.grid(True, axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.savefig('figures/move_distribution.png')
    plt.close()

def analyze_accuracy_correlation(results):
    """Analyzes correlation between hit rate and win rate"""
    plt.figure(figsize=(10, 8))
    
    win_rates = []
    accuracies = []
    
    for match, data in results.items():
        win_rates.append(data['win_rate'])
        accuracies.append(data['first_ai_accuracy'])
        win_rates.append(100 - data['win_rate'])
        accuracies.append(data['second_ai_accuracy'])
    
    plt.scatter(accuracies, win_rates, alpha=0.6)
    plt.title('Figure 4: Hit Rate vs Win Rate Correlation')
    plt.xlabel('Hit Rate (%)')
    plt.ylabel('Win Rate (%)')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Correlation line
    z = np.polyfit(accuracies, win_rates, 1)
    p = np.poly1d(z)
    plt.plot(accuracies, p(accuracies), "r--", alpha=0.5)
    
    plt.tight_layout()
    plt.savefig('figures/accuracy_correlation.png')
    plt.close()

def radar_factory(num_vars, frame='circle'):
    """Radar grafiği için özel projeksiyon oluşturur"""
    theta = np.linspace(0, 2*np.pi, num_vars, endpoint=False)
    
    class RadarTransform(PolarAxes.PolarTransform):
        def transform_path_non_affine(self, path):
            if path._vertices.shape[0] == 2:
                path = Path(path._vertices, path._codes)
            return path
    
    class RadarAxes(PolarAxes):
        name = 'radar'
        PolarTransform = RadarTransform
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.set_theta_zero_location('N')
        
        def fill(self, *args, closed=True, **kwargs):
            return super().fill(closed=closed, *args, **kwargs)
        
        def plot(self, *args, **kwargs):
            lines = super().plot(*args, **kwargs)
            for line in lines:
                self._close_line(line)
    
    register_projection(RadarAxes)
    return theta

def analyze_complexity(results):
    """Shows AI complexity analysis using radar chart"""
    plt.figure(figsize=(10, 8))
    
    # Complexity metrics
    categories = ['Time Complexity', 'Space Complexity', 'Decision Complexity']
    N = len(categories)
    theta = np.linspace(0, 2*np.pi, N, endpoint=False)
    
    # Complexity values for each AI
    complexity_data = {
        'random': [1, 1, 1],
        'bfs': [3, 2, 2],
        'greedy': [2, 2, 3],
        'monte_carlo': [4, 3, 4]
    }
    
    # Create radar chart
    ax = plt.subplot(111, polar=True)
    
    # Draw lines for each AI
    for ai, data in complexity_data.items():
        # Close the line by adding first point at the end
        values = np.concatenate((data, [data[0]]))
        angles = np.concatenate((theta, [theta[0]]))
        ax.plot(angles, values, label=ai)
        ax.fill(angles, values, alpha=0.25)
    
    # Set axes
    ax.set_xticks(theta)
    ax.set_xticklabels(categories)
    ax.set_title('Figure 5: AI Complexity Analysis')
    ax.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    
    plt.tight_layout()
    plt.savefig('figures/complexity_radar.png')
    plt.close()

def analyze_decision_strategies():
    """Shows decision-making processes of AI strategies"""
    plt.figure(figsize=(20, 15))
    
    # Create decision tree for each AI
    strategies = {
        'random': {
            'title': 'Random AI Decision Strategy',
            'steps': ['Select random square', 'Make shot', 'Record result']
        },
        'bfs': {
            'title': 'BFS AI Decision Strategy',
            'steps': ['Find hit', 'Check neighbors', 'Select new target']
        },
        'greedy': {
            'title': 'Greedy AI Decision Strategy',
            'steps': ['Create score matrix', 'Select highest score', 'Make shot']
        },
        'monte_carlo': {
            'title': 'Monte Carlo AI Decision Strategy',
            'steps': ['Run simulations', 'Select best result', 'Make shot']
        }
    }
    
    for i, (ai, strategy) in enumerate(strategies.items()):
        plt.subplot(2, 2, i+1)
        G = nx.DiGraph()
        
        # Add nodes
        for j, step in enumerate(strategy['steps']):
            G.add_node(j, label=step)
        
        # Add edges
        for j in range(len(strategy['steps'])-1):
            G.add_edge(j, j+1)
        
        # Draw graph
        pos = nx.spring_layout(G)
        nx.draw(G, pos, with_labels=True, 
                labels={j: step for j, step in enumerate(strategy['steps'])},
                node_color='lightblue', 
                node_size=2000,
                font_size=10,
                font_weight='bold')
        
        plt.title(strategy['title'])
    
    plt.tight_layout()
    plt.savefig('figures/decision_strategies.png')
    plt.close()

def create_league_table(results):
    """Shows performance summary of AIs in table format"""
    plt.figure(figsize=(15, 8))
    
    # Collect data
    data = []
    for match, match_data in results.items():
        ai1, ai2 = match.split(" vs ")
        
        # Data for AI1
        data.append({
            'AI': ai1,
            'Win Rate': match_data['win_rate'],
            'Hit Rate': match_data['first_ai_accuracy'],
            'Avg Moves': match_data['avg_moves']
        })
        
        # Data for AI2
        data.append({
            'AI': ai2,
            'Win Rate': 100 - match_data['win_rate'],
            'Hit Rate': match_data['second_ai_accuracy'],
            'Avg Moves': match_data['avg_moves']
        })
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Calculate average values for each AI
    summary = df.groupby('AI').mean().round(2)
    
    # Draw table
    plt.table(cellText=summary.values,
              rowLabels=summary.index,
              colLabels=summary.columns,
              cellLoc='center',
              loc='center')
    
    plt.title('Table I: AI Performance Summary')
    plt.axis('off')
    
    plt.tight_layout()
    plt.savefig('figures/league_table.png')
    plt.close()

def main():
    """Ana fonksiyon - tüm analizleri çalıştırır"""
    print("AI Savaş Simülasyonu Raporu oluşturuluyor...")
    
    # figures klasörünü oluştur
    if not os.path.exists('figures'):
        os.makedirs('figures')
    
    # Simülasyon sonuçlarını yükle
    results = load_results('simulation_results.json')
    
    # Analizleri çalıştır
    analyze_win_stats(results)
    analyze_accuracy(results)
    analyze_moves(results)
    analyze_accuracy_correlation(results)
    analyze_complexity(results)
    analyze_decision_strategies()
    create_league_table(results)
    
    print("\nAnalizler tamamlandı. Oluşturulan PNG dosyaları:")
    print("1. figures/win_stats.png - AI Kazanma Oranları")
    print("2. figures/hit_rates.png - AI İsabet Oranları")
    print("3. figures/move_distribution.png - Hamle Sayısı Dağılımı")
    print("4. figures/accuracy_correlation.png - İsabet Oranı vs Kazanma Oranı Korelasyonu")
    print("5. figures/complexity_radar.png - AI Karmaşıklık Analizi")
    print("6. figures/decision_strategies.png - AI Karar Stratejileri")
    print("7. figures/league_table.png - AI Performans Özeti")

if __name__ == "__main__":
    main() 