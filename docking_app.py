import streamlit as st
import subprocess
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

st.set_page_config(page_title="Simple Docking App", layout="wide")
st.title("🌍 Protein-Ligand Docking GUI with AutoDock Vina")

# --- Upload Section ---
st.sidebar.header("1. Upload Files")
receptor_file = st.sidebar.file_uploader("Upload Protein (PDBQT)", type=['pdbqt'], key="receptor")
ligand_file = st.sidebar.file_uploader("Upload Ligand (PDBQT)", type=['pdbqt'], key="ligand")

# --- Docking Parameters ---
st.sidebar.header("2. Set Docking Box")
center_x = st.sidebar.number_input("Center X", value=0.0)
center_y = st.sidebar.number_input("Center Y", value=0.0)
center_z = st.sidebar.number_input("Center Z", value=0.0)
size_x = st.sidebar.number_input("Size X", value=20.0)
size_y = st.sidebar.number_input("Size Y", value=20.0)
size_z = st.sidebar.number_input("Size Z", value=20.0)
exhaustiveness = st.sidebar.slider("Exhaustiveness", min_value=1, max_value=32, value=8)

vina_path = st.sidebar.text_input("Path to vina executable", value="vina")

# --- Run Docking ---
if st.sidebar.button("Run Docking"):
    if receptor_file and ligand_file:
        with NamedTemporaryFile(delete=False, suffix="_receptor.pdbqt") as rec_tmp, \
             NamedTemporaryFile(delete=False, suffix="_ligand.pdbqt") as lig_tmp, \
             NamedTemporaryFile(delete=False, suffix="_out.pdbqt") as out_tmp:

            rec_tmp.write(receptor_file.read())
            lig_tmp.write(ligand_file.read())
            rec_tmp.close()
            lig_tmp.close()

            vina_cmd = [
                vina_path,
                "--receptor", rec_tmp.name,
                "--ligand", lig_tmp.name,
                "--center_x", str(center_x),
                "--center_y", str(center_y),
                "--center_z", str(center_z),
                "--size_x", str(size_x),
                "--size_y", str(size_y),
                "--size_z", str(size_z),
                "--exhaustiveness", str(exhaustiveness),
                "--out", out_tmp.name
            ]

            st.code(" ".join(vina_cmd), language="bash")
            try:
                result = subprocess.run(vina_cmd, capture_output=True, text=True, check=True)
                st.success("Docking completed successfully!")
                st.text_area("Vina Output", result.stdout)

                with open(out_tmp.name, 'r') as f:
                    pdbqt_content = f.read()
                    st.download_button("Download Docked PDBQT", pdbqt_content, file_name="docked_output.pdbqt")

            except subprocess.CalledProcessError as e:
                st.error("Docking failed.")
                st.text_area("Error Output", e.stderr)

    else:
        st.warning("Please upload both receptor and ligand PDBQT files.")

# --- About Section ---
st.markdown("---")
st.markdown("""
### 📄 About this app
This simple GUI allows you to perform protein-ligand docking using [AutoDock Vina](http://vina.scripps.edu/). Upload your receptor and ligand in PDBQT format, define the grid box, and run docking directly from your browser.

- Built with **Streamlit**
- Compatible with **AutoDock Vina v1.2.x**
- Designed for basic molecular docking workflows

For 3D visualization, you can use PyMOL or UCSF Chimera to view the downloaded docking poses.
""")
