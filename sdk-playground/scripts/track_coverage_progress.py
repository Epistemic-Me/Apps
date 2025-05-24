#!/usr/bin/env python3
"""
Script to track progress against the test coverage improvement plan.
Compares current coverage with targets and generates progress reports.
"""

import json
import sys
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple
from dataclasses import dataclass
import matplotlib.pyplot as plt
import pandas as pd

@dataclass
class CoverageTarget:
    file: str
    current: float
    target: float
    priority: str
    category: str

class CoverageTracker:
    def __init__(self):
        self.targets = {
            # UI Components
            "src/ui/app.py": CoverageTarget("src/ui/app.py", 0, 70, "High", "UI"),
            "src/ui/components/metrics_display.py": CoverageTarget("src/ui/components/metrics_display.py", 16.28, 70, "High", "UI"),
            "src/ui/components/main_layout.py": CoverageTarget("src/ui/components/main_layout.py", 16.95, 70, "High", "UI"),
            "src/ui/components/conversation_turn.py": CoverageTarget("src/ui/components/conversation_turn.py", 24.07, 70, "High", "UI"),
            
            # Services
            "src/services/evaluation.py": CoverageTarget("src/services/evaluation.py", 33.33, 90, "High", "Service"),
            "src/api/endpoints.py": CoverageTarget("src/api/endpoints.py", 0, 90, "High", "Service"),
            
            # Data Generation
            "src/data/dataset_generator.py": CoverageTarget("src/data/dataset_generator.py", 34.62, 90, "Medium", "Data")
        }
        
        self.category_targets = {
            "UI": 70,
            "Service": 90,
            "Data": 90
        }
    
    def get_current_coverage(self) -> Dict:
        """Run coverage analysis and get current coverage data"""
        try:
            result = subprocess.run(
                ["pytest", "--cov=src", "--cov-report=json", "tests/"],
                capture_output=True,
                text=True
            )
            
            with open("coverage.json") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error getting coverage data: {e}")
            sys.exit(1)
    
    def calculate_progress(self, coverage_data: Dict) -> Tuple[List[Dict], Dict]:
        """Calculate progress for each file and category"""
        file_progress = []
        category_totals = {"UI": [], "Service": [], "Data": []}
        
        for file_path, target in self.targets.items():
            if file_path in coverage_data["files"]:
                current = coverage_data["files"][file_path]["summary"]["percent_covered"]
                progress = {
                    "file": file_path,
                    "current": current,
                    "target": target.target,
                    "gap": target.target - current,
                    "priority": target.priority,
                    "category": target.category
                }
                file_progress.append(progress)
                category_totals[target.category].append(current)
        
        category_progress = {
            cat: {
                "current": sum(vals) / len(vals) if vals else 0,
                "target": self.category_targets[cat],
                "gap": self.category_targets[cat] - (sum(vals) / len(vals) if vals else 0)
            }
            for cat, vals in category_totals.items()
        }
        
        return file_progress, category_progress
    
    def generate_report(self, file_progress: List[Dict], category_progress: Dict):
        """Generate a progress report"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        report = f"""
Test Coverage Progress Report
Generated: {now}

Category Progress
----------------
"""
        for cat, prog in category_progress.items():
            report += f"{cat:8} {prog['current']:6.2f}% / {prog['target']:6.2f}% (Gap: {prog['gap']:6.2f}%)\n"
        
        report += "\nFile Progress\n-------------\n"
        for prog in sorted(file_progress, key=lambda x: x["gap"], reverse=True):
            report += (
                f"{prog['file']}\n"
                f"  Current: {prog['current']:6.2f}%\n"
                f"  Target:  {prog['target']:6.2f}%\n"
                f"  Gap:     {prog['gap']:6.2f}%\n"
                f"  Priority: {prog['priority']}\n\n"
            )
        
        return report
    
    def plot_progress(self, file_progress: List[Dict], category_progress: Dict):
        """Generate progress visualizations"""
        # Category progress bar chart
        categories = list(category_progress.keys())
        current = [p["current"] for p in category_progress.values()]
        targets = [p["target"] for p in category_progress.values()]
        
        plt.figure(figsize=(10, 6))
        x = range(len(categories))
        plt.bar(x, current, width=0.4, align='edge', label='Current')
        plt.bar([i+0.4 for i in x], targets, width=0.4, align='edge', 
                alpha=0.5, label='Target')
        plt.xticks([i+0.4 for i in x], categories)
        plt.ylabel('Coverage %')
        plt.title('Coverage Progress by Category')
        plt.legend()
        plt.savefig('coverage_by_category.png')
        plt.close()
        
        # File progress heatmap
        data = {
            'File': [p["file"] for p in file_progress],
            'Current': [p["current"] for p in file_progress],
            'Target': [p["target"] for p in file_progress],
            'Gap': [p["gap"] for p in file_progress]
        }
        df = pd.DataFrame(data)
        df = df.sort_values('Gap', ascending=False)
        
        plt.figure(figsize=(12, 8))
        plt.imshow([df['Current'], df['Target']], aspect='auto', cmap='RdYlGn')
        plt.yticks([0, 1], ['Current', 'Target'])
        plt.xticks(range(len(df)), df['File'], rotation=45, ha='right')
        plt.colorbar(label='Coverage %')
        plt.title('Coverage Heatmap by File')
        plt.tight_layout()
        plt.savefig('coverage_heatmap.png')
        plt.close()
    
    def track_progress(self):
        """Track and report coverage progress"""
        coverage_data = self.get_current_coverage()
        file_progress, category_progress = self.calculate_progress(coverage_data)
        
        # Generate report
        report = self.generate_report(file_progress, category_progress)
        with open("coverage_progress.txt", "w") as f:
            f.write(report)
        
        # Generate visualizations
        self.plot_progress(file_progress, category_progress)
        
        print(report)
        print("\nGenerated reports:")
        print("- coverage_progress.txt")
        print("- coverage_by_category.png")
        print("- coverage_heatmap.png")

def main():
    tracker = CoverageTracker()
    tracker.track_progress()

if __name__ == "__main__":
    main() 