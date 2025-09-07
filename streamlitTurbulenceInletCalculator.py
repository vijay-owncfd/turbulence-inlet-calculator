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

# --- Helper Function for Robust Float Input ---
def validated_text_input(label, default_value, key=None):
    """
    Uses st.text_input for flexible entry and validates that the input
    is a positive float. Displays an error and stops execution if invalid.
    """
    user_input = st.text_input(label, value=str(default_value), key=key)
    try:
        val = float(user_input)
        if val <= 0:
            st.error(f"Input for '{label}' must be a positive number. You entered: {val}")
            st.stop()
        return val
    except (ValueError, TypeError):
        st.error(f"Invalid numeric input for '{label}'. Please enter a number like 0.01 or 1e-2.")
        st.stop()


# --- Main App ---
st.title("💨 Turbulence Inlet Conditions Calculator")
st.subheader("A web-based utility to calculate turbulent boundary conditions for CFD simulations.")
st.markdown("Born to Vijay and Gemini on 7th Sep 2025. Last updated: 7th Sep 2025.")
st.header("⬅️  Select your model and application type from the sidebar to begin.")

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
    rho = validated_text_input("Density (ρ) in kg/m³", 1.225)
    mu = validated_text_input("Dynamic Viscosity (μ) in Pa-s", 1.81e-5)


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
            diam = validated_text_input("Diameter (m)", 1.0)
            Dh = diam
            A = (math.pi / 4) * diam**2
        elif cross_sec_choice == 2: # Annular
            Din = validated_text_input("Inner Diameter (m)", 0.5)
            Dout = validated_text_input("Outer Diameter (m)", 1.0)
            if Dout > Din:
                Dh = Dout - Din
                A = (math.pi / 4) * (Dout**2 - Din**2)
            else:
                st.error("Outer diameter must be greater than inner diameter.")
                st.stop()
        elif cross_sec_choice == 3: # Square
            side = validated_text_input("Side Length (m)", 1.0)
            Dh = side
            A = side**2
        elif cross_sec_choice == 4: # Rectangular
            a = validated_text_input("Width (m)", 2.0)
            b = validated_text_input("Height (m)", 1.0)
            Dh = 2 * a * b / (a + b)
            A = a * b
        elif cross_sec_choice == 5: # 2D Channel
            a = validated_text_input("Channel Height (m)", 1.0)
            Dh = 2 * a
            A = None
            is_2d_channel = True
        elif cross_sec_choice == 6: # Other
            A_in = validated_text_input("Cross-sectional Area (m²)", 1.0)
            P_in = validated_text_input("Wetted Perimeter (m)", 4.0)
            Dh = 4 * A_in / P_in
            A = A_in
        elif cross_sec_choice == 7: # Specified Dh
            Dh = validated_text_input("Hydraulic Diameter (m)", 1.0)
            A = (math.pi / 4) * Dh**2
            st.info("Area is assumed based on a circular cross-section for flow rate calculations.")

    with col2:
        st.subheader("Flow Rate / Velocity")
        if is_2d_channel:
            st.info("For a 2D channel, only velocity can be specified.")
            U = validated_text_input("Inlet Velocity (m/s)", 10.0)
        else:
            vel_type_options = {1: "Velocity", 2: "Mass Flow Rate", 3: "Volume Flow Rate"}
            vel_type_choice = st.selectbox(
                "Boundary Condition Type:",
                options=list(vel_type_options.keys()),
                format_func=lambda x: vel_type_options[x]
            )
            if vel_type_choice == 1:
                U = validated_text_input("Velocity (m/s)", 10.0)
            elif vel_type_choice == 2:
                mDot = validated_text_input("Mass Flow Rate (kg/s)", 1.0)
                U = mDot / (rho * A)
            elif vel_type_choice == 3:
                QDot = validated_text_input("Volume Flow Rate (m³/s)", 1.0)
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
            delta_99 = validated_text_input("Boundary Layer Thickness (m)", 0.1)
        l = 0.4 * delta_99
    elif l_choice == 3:
        l = validated_text_input("Characteristic Length (m)", 0.01)

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
        U = validated_text_input("Reference Velocity (U_ref) in m/s", 10.0)


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


