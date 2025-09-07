import streamlit as st
import math

# --- Constants ---
C_MU = 0.09  # Standard k-epsilon model constant

# --- App Configuration ---
st.set_page_config(
    page_title="Turbulence Inlet Calculator",
    page_icon="💨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Main App ---

st.title("💨 Turbulence Inlet Conditions Calculator")
st.markdown(
    "A web-based utility to calculate turbulent boundary conditions for CFD simulations. "
    "Select your model and application type from the sidebar to begin. \n Born on "
    "7th Sep 2025 to Vijay and Gemini. Last update 7th Sep 2025."
)
st.subtitle("Vijay and Gemini")

# --- Sidebar for Core Inputs ---
with st.sidebar:
    st.header("1. Core Setup")
    
    model_options = {1: "Spalart-Allmaras", 2: "k-epsilon based", 3: "k-omega based"}
    model_choice = st.selectbox(
        "Select the turbulence model:",
        options=list(model_options.keys()),
        format_func=lambda x: model_options[x]
    )

    app_options = {
        1: "Wall bounded flow (Pipe / Channel)",
        2: "Inlet into a domain (e.g., Jet)",
        3: "External aerodynamics (e.g., Airfoil)",
        4: "High speed flows inside complex geometries",
        5: "Flow inside pumps or compressors",
        6: "Unsure / General case"
    }
    app_choice = st.selectbox(
        "Choose the application type:",
        options=list(app_options.keys()),
        format_func=lambda x: app_options[x]
    )

    st.header("2. Fluid Properties")
    # Using general format specifiers (%f, %g) to prevent input issues
    rho = st.number_input("Density (ρ) in kg/m³", min_value=1e-9, value=1.225, format="%f", step=None)
    mu = st.number_input("Dynamic Viscosity (μ) in Pa-s", min_value=1e-9, value=1.81e-5, format="%g", step=None)

# --- Main Panel for Detailed Inputs and Results ---

# Initialize variables
Dh, A, U, l, I, visc_rat, k, omega, epsilon, Re = (None,) * 10
is_2d_channel = False

# --- Case 1: Internal Flows (Requires detailed geometry and velocity) ---
if app_choice in [1, 2]:
    st.header("3. Inlet & Flow Specification")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Inlet Geometry")
        cross_sec_options = {
            1: "Circular", 2: "Annular", 3: "Square", 4: "Rectangular",
            5: "2D Channel", 6: "Other (Area/Perimeter)", 7: "Specified Hydraulic Diameter"
        }
        cross_sec_choice = st.selectbox(
            "Inlet Cross-Section:",
            options=list(cross_sec_options.keys()),
            format_func=lambda x: cross_sec_options[x]
        )

        # Conditional Geometry Inputs
        if cross_sec_choice == 1: # Circular
            diam = st.number_input("Diameter (m)", min_value=1e-9, value=1.0, format="%f", step=None)
            Dh = diam
            A = (math.pi / 4) * diam**2
        elif cross_sec_choice == 2: # Annular
            Din = st.number_input("Inner Diameter (m)", min_value=1e-9, value=0.5, format="%f", step=None)
            Dout = st.number_input("Outer Diameter (m)", min_value=1e-9, value=1.0, format="%f", step=None)
            if Dout > Din:
                Dh = Dout - Din
                A = (math.pi / 4) * (Dout**2 - Din**2)
            else:
                st.error("Outer diameter must be greater than inner diameter.")
                st.stop()
        elif cross_sec_choice == 3: # Square
            side = st.number_input("Side Length (m)", min_value=1e-9, value=1.0, format="%f", step=None)
            Dh = side
            A = side**2
        elif cross_sec_choice == 4: # Rectangular
            a = st.number_input("Width (m)", min_value=1e-9, value=2.0, format="%f", step=None)
            b = st.number_input("Height (m)", min_value=1e-9, value=1.0, format="%f", step=None)
            Dh = 2 * a * b / (a + b)
            A = a * b
        elif cross_sec_choice == 5: # 2D Channel
            a = st.number_input("Channel Height (m)", min_value=1e-9, value=1.0, format="%f", step=None)
            Dh = 2 * a
            A = None
            is_2d_channel = True
        elif cross_sec_choice == 6: # Other
            A_in = st.number_input("Cross-sectional Area (m²)", min_value=1e-9, value=1.0, format="%f", step=None)
            P_in = st.number_input("Wetted Perimeter (m)", min_value=1e-9, value=4.0, format="%f", step=None)
            Dh = 4 * A_in / P_in
            A = A_in
        elif cross_sec_choice == 7: # Specified Dh
            Dh = st.number_input("Hydraulic Diameter (m)", min_value=1e-9, value=1.0, format="%f", step=None)
            A = (math.pi / 4) * Dh**2
            st.info("Area is assumed based on a circular cross-section for flow rate calculations.")

    with col2:
        st.subheader("Flow Rate / Velocity")
        if is_2d_channel:
            st.info("For a 2D channel, only velocity can be specified.")
            U_in = st.number_input("Inlet Velocity (m/s)", min_value=1e-9, value=10.0, format="%f", step=None)
            U = U_in
        else:
            vel_type_options = {1: "Velocity", 2: "Mass Flow Rate", 3: "Volume Flow Rate"}
            vel_type_choice = st.selectbox(
                "Boundary Condition Type:",
                options=list(vel_type_options.keys()),
                format_func=lambda x: vel_type_options[x]
            )
            if vel_type_choice == 1:
                U_in = st.number_input("Velocity (m/s)", min_value=1e-9, value=10.0, format="%f", step=None)
                U = U_in
            elif vel_type_choice == 2:
                mDot = st.number_input("Mass Flow Rate (kg/s)", min_value=1e-9, value=1.0, format="%f", step=None)
                U = mDot / (rho * A)
            elif vel_type_choice == 3:
                QDot = st.number_input("Volume Flow Rate (m³/s)", min_value=1e-9, value=1.0, format="%f", step=None)
                U = QDot / A

    st.subheader("Turbulence Generation")
    l_choice_options = {
        1: "Cross-section based (Standard)",
        2: "Boundary Layer Thickness",
        3: "Characteristic Length (e.g., perforations)"
    }
    l_choice = st.selectbox(
        "Primary source of turbulence:",
        options=list(l_choice_options.keys()),
        format_func=lambda x: l_choice_options[x]
    )
    if l_choice == 1:
        l = 0.07 * Dh
    elif l_choice == 2:
        delta_choice = st.radio(
            "Boundary layer thickness (δ):",
            ["Estimate for fully developed flow", "Specify a value"],
            horizontal=True
        )
        if delta_choice == "Estimate for fully developed flow":
            delta_99 = Dh / 2.0
            st.write(f"Estimated δ for fully developed flow: **{delta_99:.4g} m**")
        else:
            delta_99 = st.number_input("Boundary Layer Thickness (m)", min_value=1e-9, value=0.1, format="%f", step=None)
        l = 0.4 * delta_99
    elif l_choice == 3:
        l_in = st.number_input("Characteristic Length (m)", min_value=1e-9, value=0.01, format="%f", step=None)
        l = l_in


# --- Case 2: External / General Flows ---
else:
    st.header("3. Flow Specification")
    st.info("For external or general cases, turbulence levels are estimated based on typical scenarios.")
    if app_choice == 3:      # External aerodynamics
        I, visc_rat = 0.01, 1.0
    elif app_choice in [4, 5]: # High speed / Pumps
        I, visc_rat = 0.1, 10.0
    else:                     # Unsure / General
        I, visc_rat = 0.05, 5.0
    
    if model_choice > 1:
        st.write("To compute Dirichlet values (k, ω, ε), a reference velocity is needed.")
        U = st.number_input("Reference Velocity (U_ref) in m/s", min_value=1e-9, value=10.0, format="%f", step=None)


# --- Calculation Trigger ---
if st.button("Calculate Turbulence Properties", type="primary"):
    # Perform calculations only when the button is pressed
    if app_choice in [1, 2]: # Internal flows
        Re = rho * U * Dh / mu
        I = 0.16 * (Re ** -0.125)
        k = 1.5 * (U * I)**2
        if k > 0 and l > 0:
            omega = (C_MU ** -0.25) * math.sqrt(k) / l
            epsilon = C_MU * k * omega
            mut = rho * k / omega
            visc_rat = mut / mu
        else:
            visc_rat = 1.0 # Default fallback
    
    # --- Display Results ---
    st.header("Results")
    st.success("Calculations complete. See recommended boundary conditions and reference values below.")

    res_col1, res_col2 = st.columns(2)
    with res_col1:
        st.subheader("Recommended Boundary Conditions")
        if model_choice == 1:
            st.metric(label="Turbulent Viscosity Ratio (μ_t / μ)", value=f"{visc_rat:.4g}")
            st.info("For Spalart-Allmaras, specifying the viscosity ratio is often the most robust option.")
        elif app_choice in [1, 2]: # k-omega/eps, internal
            st.metric(label="Turbulent Intensity (I)", value=f"{I:.4f} ({I*100:.2f} %)")
            st.metric(label="Turbulent Length Scale (l)", value=f"{l:.4g} m")
            st.info("For k-ε and k-ω models in internal flows, Intensity and Length Scale are robust.")
        else: # k-omega/eps, external
            st.metric(label="Turbulent Intensity (I)", value=f"{I:.4f} ({I*100:.2f} %)")
            st.metric(label="Turbulent Viscosity Ratio (μ_t / μ)", value=f"{visc_rat:.4g}")
            st.info("For k-ε and k-ω models in external flows, Intensity and Viscosity Ratio are robust.")

    with res_col2:
        st.subheader("Calculated Flow Properties")
        if Re:
            st.metric(label="Reynolds Number (Re)", value=f"{Re:.4g}")
        if U:
            st.metric(label="Bulk Velocity (U)", value=f"{U:.4g} m/s")
        if Dh:
            st.metric(label="Hydraulic Diameter (Dh)", value=f"{Dh:.4g} m")

    with st.expander("Show Reference Dirichlet Values (for advanced use)"):
        st.warning(
            "**Disclaimer:** These are direct values calculated from the inputs. "
            "It is often more stable to use the recommended conditions above if your solver supports them."
        )
        # Calculate dirichlet values if not already done
        if k is None and U is not None:
             k = 1.5 * (U * I)**2
             mut = visc_rat * mu
             omega = rho * k / mut if mut > 0 else float('inf')
             epsilon = C_MU * k * omega
        
        dir_col1, dir_col2, dir_col3 = st.columns(3)
        with dir_col1:
            if model_choice == 1:
                 nuTilda = visc_rat * mu / rho
                 st.markdown(f"**S-A Variable (ν̃)**: `{nuTilda:.4g}` m²/s")
            
            if model_choice in [2, 3]:
                st.markdown(f"**Turb. Kinetic Energy (k)**: `{k:.4g}` m²/s²")

        with dir_col2:
             if model_choice == 2:
                 st.markdown(f"**Dissipation Rate (ε)**: `{epsilon:.4g}` m²/s³")

        with dir_col3:
             if model_choice == 3:
                 st.markdown(f"**Specific Dissipation Rate (ω)**: `{omega:.4g}` 1/s")


