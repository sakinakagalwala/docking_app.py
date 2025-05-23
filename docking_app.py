import streamlit as st
import subprocess
import tempfile
import os

st.title("Simple Molecular Docking App")

# Upload protein (PDBQT) and ligand (PDBQT)
protein = st.file_uploader("Upload protein (PDBQT)", type=["pdbqt"])
ligand = st.file_uploader("Upload ligand (PDBQT)", type=["pdbqt"])

if protein and ligand:
    with tempfile.TemporaryDirectory() as tmpdir:
        protein_path = os.path.join(tmpdir, "receptor.pdbqt")
        ligand_path = os.path.join(tmpdir, "ligand.pdbqt")
        out_path = os.path.join(tmpdir, "out.pdbqt")

        # Save uploaded files
        with open(protein_path, "wb") as f:
            f.write(protein.getbuffer())
        with open(ligand_path, "wb") as f:
            f.write(ligand.getbuffer())

        st.info("Running AutoDock Vina...")
        
        # Run AutoDock Vina subprocess - change --center_x/y/z and --size_x/y/z as needed
        cmd = [
            "vina",
            "--receptor", protein_path,
            "--ligand", ligand_path,
            "--out", out_path,
            "--center_x", "0",
            "--center_y", "0",
            "--center_z", "0",
            "--size_x", "20",
            "--size_y", "20",
            "--size_z", "20",
            "--exhaustiveness", "8",
            "--num_modes", "3"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            st.success("Docking complete!")
            st.text(result.stdout)

            # Read docked output (top pose)
            with open(out_path, "r") as f:
                docked_pose = f.read()

            # Show docking scores summary from output
            st.subheader("Docking Output Summary")
            lines = result.stdout.splitlines()
            scores = [line for line in lines if "mode" in line.lower()]
            st.text("\n".join(scores))

            # 3D visualization using 3dmol.js embedded in HTML
            st.subheader("3D Visualization of Top Docked Pose")

            def show_3dmol_viewer(pdbqt_string):
                html = f"""
                <html>
                <head>
                  <script src="https://3dmol.org/build/3Dmol-min.js"></script>
                </head>
                <body>
                  <div id="container" style="width: 700px; height: 500px; position: relative;"></div>
                  <script>
                    let viewer = $3Dmol.createViewer("container", {{backgroundColor: "white"}});
                    viewer.addModel(`{pdbqt_string}`, "pdbqt");
                    viewer.setStyle({{}}, {{stick: {{}}}});
                    viewer.zoomTo();
                    viewer.render();
                  </script>
                </body>
                </html>
                """
                st.components.v1.html(html, height=550)

            show_3dmol_viewer(docked_pose)

        except subprocess.CalledProcessError as e:
            st.error(f"Error running AutoDock Vina:\n{e.stderr}")

else:
    st.info("Upload both protein and ligand PDBQT files to start docking.")
