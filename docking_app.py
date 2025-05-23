import streamlit as st
import subprocess
import tempfile
import os
import pandas as pd

st.set_page_config(page_title="Molecular Docking App", layout="wide")

st.title("🧬 Molecular Docking with AutoDock Vina")

st.markdown("""
Upload your **protein** and **ligand** files (in PDBQT format recommended) to run docking.
Adjust docking parameters in the sidebar and visualize top binding poses interactively.
""")

# Sidebar parameters
st.sidebar.header("Docking Parameters")
exhaustiveness = st.sidebar.slider("Exhaustiveness", 1, 20, 8)
num_modes = st.sidebar.slider("Number of modes", 1, 10, 5)
center_x = st.sidebar.number_input("Center X (Å)", value=0.0, format="%.2f")
center_y = st.sidebar.number_input("Center Y (Å)", value=0.0, format="%.2f")
center_z = st.sidebar.number_input("Center Z (Å)", value=0.0, format="%.2f")
size_x = st.sidebar.number_input("Size X (Å)", value=20.0, min_value=1.0, format="%.2f")
size_y = st.sidebar.number_input("Size Y (Å)", value=20.0, min_value=1.0, format="%.2f")
size_z = st.sidebar.number_input("Size Z (Å)", value=20.0, min_value=1.0, format="%.2f")

# File uploads
protein_file = st.file_uploader("Upload Protein (PDBQT)", type=["pdbqt", "pdb"])
ligand_file = st.file_uploader("Upload Ligand (PDBQT, MOL2)", type=["pdbqt", "mol2", "mol"])

def convert_to_pdbqt(input_path, output_path):
    # Requires obabel installed in system path
    try:
        subprocess.run(
            ["obabel", "-ipdb", input_path, "-opdbqt", "-O", output_path],
            check=True,
            capture_output=True
        )
        return True
    except Exception as e:
        st.error(f"Open Babel conversion failed: {e}")
        return False

def run_vina(protein_path, ligand_path, out_path):
    cmd = [
        "vina",
        "--receptor", protein_path,
        "--ligand", ligand_path,
        "--out", out_path,
        "--center_x", str(center_x),
        "--center_y", str(center_y),
        "--center_z", str(center_z),
        "--size_x", str(size_x),
        "--size_y", str(size_y),
        "--size_z", str(size_z),
        "--exhaustiveness", str(exhaustiveness),
        "--num_modes", str(num_modes)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result

def parse_vina_output(output_text):
    """
    Extract docking modes and scores from Vina output.
    Returns pandas DataFrame with mode, affinity (kcal/mol).
    """
    lines = output_text.splitlines()
    data = []
    for line in lines:
        if line.strip().startswith("mode"):
            parts = line.split()
            if len(parts) >= 3:
                mode = int(parts[1])
                affinity = float(parts[2])
                data.append({"Mode": mode, "Affinity (kcal/mol)": affinity})
    df = pd.DataFrame(data)
    return df

def show_3dmol(pdbqt_string):
    html = f"""
    <html>
    <head>
      <script src="https://3dmol.org/build/3Dmol-min.js"></script>
    </head>
    <body>
      <div id="viewer" style="width:700px; height:500px; position: relative;"></div>
      <script>
        let viewer = $3Dmol.createViewer("viewer", {{backgroundColor: "white"}});
        viewer.addModel(`{pdbqt_string}`, "pdbqt");
        viewer.setStyle({{}}, {{stick: {{}}}});
        viewer.zoomTo();
        viewer.render();
      </script>
    </body>
    </html>
    """
    st.components.v1.html(html, height=550)

if protein_file and ligand_file:
    with tempfile.TemporaryDirectory() as tmpdir:
        # Save uploaded files
        protein_path = os.path.join(tmpdir, "protein.pdbqt")
        ligand_path = os.path.join(tmpdir, "ligand.pdbqt")
        out_path = os.path.join(tmpdir, "docked_out.pdbqt")

        # Handle protein file conversion if needed
        protein_ext = protein_file.name.split(".")[-1].lower()
        if protein_ext != "pdbqt":
            prot_tmp = os.path.join(tmpdir, "protein_input.pdb")
            with open(prot_tmp, "wb") as f:
                f.write(protein_file.getbuffer())
            converted = convert_to_pdbqt(prot_tmp, protein_path)
            if not converted:
                st.stop()
        else:
            with open(protein_path, "wb") as f:
                f.write(protein_file.getbuffer())

        # Handle ligand file conversion if needed
        ligand_ext = ligand_file.name.split(".")[-1].lower()
        if ligand_ext != "pdbqt":
            lig_tmp = os.path.join(tmpdir, "ligand_input.mol2")
            with open(lig_tmp, "wb") as f:
                f.write(ligand_file.getbuffer())
            converted = convert_to_pdbqt(lig_tmp, ligand_path)
            if not converted:
                st.stop()
        else:
            with open(ligand_path, "wb") as f:
                f.write(ligand_file.getbuffer())

        # Run docking
        st.info("Running AutoDock Vina docking...")
        vina_result = run_vina(protein_path, ligand_path, out_path)
        if vina_result.returncode != 0:
            st.error(f"Vina error:\n{vina_result.stderr}")
            st.stop()

        st.success("Docking finished successfully!")

        # Parse and show docking scores
        df_scores = parse_vina_output(vina_result.stdout)
        if df_scores.empty:
            st.warning("No docking scores found in output.")
        else:
            st.subheader("Docking Scores")
            st.dataframe(df_scores)

        # Load docked poses for visualization
        with open(out_path, "r") as f:
            docked_data = f.read()

        st.subheader("3D Viewer of Top Docked Pose")
        show_3dmol(docked_data)

else:
    st.info("Please upload both protein and ligand files to proceed.")
