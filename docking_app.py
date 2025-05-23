import streamlit as st
import subprocess
import tempfile
import os
import py3dmol

st.set_page_config(page_title="Protein-Ligand Docking App", layout="wide")

st.markdown("""
    <h1 style='text-align: center; color: #2c3e50;'>Protein-Ligand Docking Web App</h1>
    <p style='text-align: center; font-size: 18px;'>Upload your protein and ligand files, run AutoDock Vina docking, and visualize the results in 3D!</p>
""", unsafe_allow_html=True)

# Sidebar inputs
st.sidebar.header("Docking Parameters")

protein_file = st.sidebar.file_uploader("Upload Protein (PDBQT format)", type=["pdbqt"])
ligand_file = st.sidebar.file_uploader("Upload Ligand (PDBQT format)", type=["pdbqt"])

center_x = st.sidebar.number_input("Grid center X", value=0.0, step=0.1)
center_y = st.sidebar.number_input("Grid center Y", value=0.0, step=0.1)
center_z = st.sidebar.number_input("Grid center Z", value=0.0, step=0.1)

size_x = st.sidebar.number_input("Grid size X (Å)", value=20.0, step=0.1)
size_y = st.sidebar.number_input("Grid size Y (Å)", value=20.0, step=0.1)
size_z = st.sidebar.number_input("Grid size Z (Å)", value=20.0, step=0.1)

exhaustiveness = st.sidebar.slider("Exhaustiveness", 1, 20, 8)

run_docking = st.sidebar.button("Run Docking")

if protein_file and ligand_file:
    st.markdown("### Uploaded Files:")
    st.write(f"**Protein:** {protein_file.name}")
    st.write(f"**Ligand:** {ligand_file.name}")
else:
    st.info("Upload both protein and ligand PDBQT files to enable docking.")

def run_vina(protein_path, ligand_path, center_x, center_y, center_z, size_x, size_y, size_z, exhaustiveness):
    output_path = tempfile.mktemp(suffix=".pdbqt")
    command = [
        "vina",
        "--receptor", protein_path,
        "--ligand", ligand_path,
        "--center_x", str(center_x),
        "--center_y", str(center_y),
        "--center_z", str(center_z),
        "--size_x", str(size_x),
        "--size_y", str(size_y),
        "--size_z", str(size_z),
        "--exhaustiveness", str(exhaustiveness),
        "--out", output_path,
        "--log", output_path + ".log",
        "--num_modes", "5"
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    return output_path, result.stdout, result.stderr

if run_docking:
    if not protein_file or not ligand_file:
        st.error("Please upload both protein and ligand files.")
    else:
        # Save uploaded files temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdbqt") as f_prot:
            f_prot.write(protein_file.read())
            protein_path = f_prot.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdbqt") as f_lig:
            f_lig.write(ligand_file.read())
            ligand_path = f_lig.name

        st.info("Running AutoDock Vina... This may take a while.")
        with st.spinner("Docking in progress..."):
            out_path, stdout, stderr = run_vina(
                protein_path, ligand_path,
                center_x, center_y, center_z,
                size_x, size_y, size_z,
                exhaustiveness)

        st.success("Docking completed!")

        if stderr:
            st.warning(f"Warnings/errors:\n{stderr}")

        # Read docking output file
        with open(out_path, "r") as f:
            docked_pose = f.read()

        # Show docking scores from stdout
        st.subheader("Docking Log Output")
        st.text(stdout)

        # 3D visualization of docked ligand
        st.subheader("3D Visualization of Docked Ligand")
        view = py3dmol.view(width=700, height=500)
        view.addModel(docked_pose, "pdbqt")
        view.setStyle({'stick': {}})
        view.zoomTo()
        view.show()
        st.components.v1.html(view.js(), height=550)

        # Download docked output
        st.download_button(
            label="Download Docked Poses (PDBQT)",
            data=docked_pose,
            file_name="docked_output.pdbqt",
            mime="text/plain"
        )

        # Cleanup temp files
        os.unlink(protein_path)
        os.unlink(ligand_path)
        os.unlink(out_path)
        if os.path.exists(out_path + ".log"):
            os.unlink(out_path + ".log")

else:
    st.info("Set parameters and click 'Run Docking' to start.")

