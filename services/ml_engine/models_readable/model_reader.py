import joblib
import pickle
import json
import os
import sys

# Ensure custom classes can be imported (e.g. WoEBinner)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(script_dir)))
sys.path.insert(0, project_root)

def create_readable_models():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = script_dir
    models_dir = os.path.join(os.path.dirname(script_dir), "models")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    binner_path = os.path.join(models_dir, "woe_binner.pkl")
    model_path = os.path.join(models_dir, "credit_risk_model.joblib")
    
    print(f"Reading from: {models_dir}")
    print(f"Exporting to: {output_dir}")
    
    # 1. READ WOE BINNER
    if os.path.exists(binner_path):
        try:
            with open(binner_path, "rb") as f:
                binner = pickle.load(f)
            
            binner_data = {
                "information_value_table": getattr(binner, "iv_table", {}),
                "woe_mapping_rules": getattr(binner, "woe_maps", {}),
                "numerical_bin_edges": getattr(binner, "bin_edges", {})
            }
            
            out_binner = os.path.join(output_dir, "woe_binner_readable.json")
            with open(out_binner, "w", encoding="utf-8") as f:
                json.dump(binner_data, f, indent=4, ensure_ascii=False)
            print(f" [OK] Saved WoE Binner data to: {out_binner}")
        except Exception as e:
            print(f" [ERROR] Could not read woe_binner.pkl: {e}")
    else:
        print(" [WARN] woe_binner.pkl not found")

    # 2. READ XGBOOST MODEL
    if os.path.exists(model_path):
        try:
            model = joblib.load(model_path)
            
            # 2.1 Feature Importances
            if hasattr(model, "feature_importances_") and hasattr(model, "feature_names_in_"):
                importances = dict(zip(model.feature_names_in_, model.feature_importances_))
                # Sort by importance
                importances = {k: float(v) for k, v in sorted(importances.items(), key=lambda item: item[1], reverse=True)}
                
                out_feat = os.path.join(output_dir, "xgboost_feature_importances.json")
                with open(out_feat, "w", encoding="utf-8") as f:
                    json.dump(importances, f, indent=4)
                print(f" [OK] Saved Feature Importances to: {out_feat}")
            
            # 2.2 XGBoost Trees structure (Mermaid Parsing - 3 Subgraphs in 1 File)
            if hasattr(model, "get_booster"):
                booster = model.get_booster()
                trees = booster.get_dump()
                
                # Trích xuất 3 cây: Đầu, Giữa và Cuối
                total_trees = len(trees)
                target_indices = [0, total_trees // 2, total_trees - 1]
                
                out_mmd = os.path.join(output_dir, "xgboost_sampled_trees.mmd")
                
                with open(out_mmd, "w", encoding="utf-8") as f:
                    f.write("graph TD\n")
                    f.write("    %% Bản vẽ gộp 3 cây quyết định ở 3 giai đoạn học tập khác nhau\n\n")
                    
                    for idx in target_indices:
                        tree_text = trees[idx]
                        
                        f.write(f"    subgraph Tree_{idx} [\"Cây quyết định số {idx}\"]\n")
                        f.write(f"        direction TB\n")
                        
                        lines = tree_text.strip().split('\n')
                        for line in lines:
                            line = line.strip()
                            if not line:
                                continue
                                
                            # Nhánh: "0:[loan_grade<1.5] yes=1,no=2,missing=1"
                            if "yes=" in line:
                                node_id = line.split(":")[0]
                                condition = line.split("[")[1].split("]")[0]
                                # Escaping HTML characters for Mermaid
                                condition = condition.replace("<", "&lt;").replace(">", "&gt;")
                                
                                yes_id = line.split("yes=")[1].split(",")[0]
                                no_id = line.split("no=")[1].split(",")[0]
                                
                                f.write(f'        T{idx}N{node_id}["{condition}"]\n')
                                f.write(f'        T{idx}N{node_id} -- "yes" --> T{idx}N{yes_id}\n')
                                f.write(f'        T{idx}N{node_id} -- "no" --> T{idx}N{no_id}\n')
                                
                            # Lá: "3:leaf=0.07142"
                            elif "leaf=" in line:
                                node_id = line.split(":")[0]
                                leaf_val = line.split("leaf=")[1]
                                f.write(f'        T{idx}N{node_id}(("Lá: {leaf_val}"))\n')
                                f.write(f'        style T{idx}N{node_id} fill:#fca5a5,stroke:#b91c1c,stroke-width:2px\n')
                                
                        f.write("    end\n\n")
                        
                print(f" [OK] Saved Merged XGBoost Trees Diagram to: {out_mmd}")
                
        except Exception as e:
            print(f" [ERROR] Could not read credit_risk_model.joblib: {e}")
    else:
        print(" [WARN] credit_risk_model.joblib not found")

if __name__ == "__main__":
    create_readable_models()
