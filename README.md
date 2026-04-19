# FC 26 SBC Solver

Solver de SBC (Squad Building Challenges) para EA Sports FC 26 usando programação por restrições (CP-SAT do Google OR-Tools).

Encontra o **squad mais barato** que atende todos os requisitos de um SBC — rating mínimo, química, ligas, nações, clubes, versões, etc.

## Instalação

```bash
pip install -r requirements.txt
```

## Uso

```python
from data.dataset_factory import DatasetFactory, DatasetSources
from src.sbc_solver.ea_fc_sbc_solver import EaFcSbcSolver
from src.utils.formations import Formations
from src.solution_display.console_display import SbcSolutionConsoleDisplay

if __name__ == "__main__":
    dataset = DatasetFactory.create(DatasetSources.CSV)
    formation = Formations["4-4-2"]

    solver = EaFcSbcSolver(dataset, formation)
    solver.set_min_overall_of_squad(80)
    solver.set_min_unique_leagues(5)
    solver.set_min_unique_nations(5)
    solver.set_min_rare_cards(2)
    solver.set_min_team_chemistry(5)

    sbc_cards = solver.solve()

    display = SbcSolutionConsoleDisplay(sbc_cards, formation)
    display.display()
```

## Restrições disponíveis

| Método | Descrição |
|--------|-----------|
| `set_min_overall_of_squad(rating)` | Rating mínimo do squad |
| `set_min_cards_with_overall(rating, count)` | Mínimo de jogadores com rating X |
| `set_min_team_chemistry(chem)` | Química mínima do time |
| `set_exact_unique_nations(n)` | Número exato de nações únicas |
| `set_min_unique_nations(n)` | Mínimo de nações únicas |
| `set_max_unique_nations(n)` | Máximo de nações únicas |
| `set_exact_unique_leagues(n)` | Número exato de ligas únicas |
| `set_min_unique_leagues(n)` | Mínimo de ligas únicas |
| `set_max_unique_leagues(n)` | Máximo de ligas únicas |
| `set_min_rare_cards(n)` | Mínimo de cartas raras |
| `set_min_cards_with_version(version, n)` | Mínimo de cartas de uma versão |
| `set_min_cards_with_league(league, n)` | Mínimo de cartas de uma liga |
| `set_min_cards_with_nation(nation, n)` | Mínimo de cartas de uma nação |
| `set_min_cards_with_club(club, n)` | Mínimo de cartas de um clube |

## Formações suportadas

35 formações: 3-4-3, 4-3-3 (5 variantes), 4-4-2 (2 variantes), 4-2-3-1 (2 variantes), 5-3-2, etc. Veja todas em `src/utils/formations.py`.

## Dados dos jogadores

O solver usa dados de jogadores em CSV com as colunas: Name, Version, Club, League, Nationality, Position, Overall Rating, Price, Futwiz Link, + stats.

Para funcionar com FC 26, é necessário um CSV atualizado com jogadores e preços do FC 26. Coloque o arquivo em `data/csv/fc26_players.csv`.

## Estrutura do projeto

```
fc26-sbc-solver/
├── data/
│   ├── csv/
│   │   ├── csv_utils.py          # Leitura e preprocessamento do CSV
│   │   ├── card_data_template.py  # Templates de colunas dos cards
│   │   └── fc26_players.csv      # Dados dos jogadores FC26
│   └── dataset_factory.py        # Factory para carregar dataset
├── src/
│   ├── main.py                   # Entry point
│   ├── sbc_solver/
│   │   ├── ea_fc_sbc_solver.py   # Solver CP-SAT
│   │   └── exceptions.py         # Exceções customizadas
│   ├── solution_display/
│   │   ├── console_display.py    # Display em tabela no console
│   │   ├── webbrowser_display.py # Abre links no navegador
│   │   └── sbc_solution_display_if.py
│   └── utils/
│       └── formations.py         # 35 formações disponíveis
├── setup.py
└── requirements.txt
```

## Licença

MIT
