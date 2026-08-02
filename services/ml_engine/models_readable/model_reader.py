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
            
            # 2.2 XGBoost Trees structure
            if hasattr(model, "get_booster"):
                booster = model.get_booster()
                trees = booster.get_dump()
                
                out_trees = os.path.join(output_dir, "xgboost_trees_structure.txt")
                with open(out_trees, "w", encoding="utf-8") as f:
                    f.write(f"XGBOOST MODEL STRUCTURE\n")
                    f.write(f"Total Trees: {len(trees)}\n")
                    f.write("="*50 + "\n\n")
                    # Chỉ in 3 cây đầu tiên để file không quá nặng, dễ xem
                    for i, tree in enumerate(trees[:3]):
                        f.write(f"--- TREE #{i} ---\n")
                        f.write(tree)
                        f.write("\n")
                    f.write("\n(Note: Only showing first 3 trees out of 300 for readability)\n")
                    
                print(f" [OK] Saved XGBoost Trees (top 3) to: {out_trees}")
                
        except Exception as e:
            print(f" [ERROR] Could not read credit_risk_model.joblib: {e}")
    else:
        print(" [WARN] credit_risk_model.joblib not found")

if __name__ == "__main__":
    create_readable_models()
