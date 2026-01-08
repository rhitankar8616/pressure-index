"""
How It Works Page
Explanation of Pressure Index methodology
"""

import streamlit as st
import os
import sys
import base64

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.components.ui_components import render_footer


def display_pdf(pdf_path):
    """Display a PDF file in the Streamlit app"""

    # Check if file exists
    if not os.path.exists(pdf_path):
        st.error(f"PDF file not found at: {pdf_path}")
        st.info("Please place your research paper PDF in the 'data' folder and name it 'research_paper.pdf'")
        return

    # Read PDF file
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    # Provide download button
    st.download_button(
        label="📄 Download Research Paper (PDF)",
        data=pdf_bytes,
        file_name="Pressure_Index_Research_Paper.pdf",
        mime="application/pdf",
        use_container_width=True
    )

    st.markdown("---")

    # Try to display PDF using iframe (works in most browsers)
    base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')

    # Create tabs for different viewing options
    view_tab1, view_tab2 = st.tabs(["📖 View PDF", "ℹ️ Paper Information"])

    with view_tab1:
        # Embed PDF in iframe with full width
        pdf_display = f"""
        <div style="width: 100%; height: 1200px; overflow: auto;">
            <iframe
                src="data:application/pdf;base64,{base64_pdf}#view=FitH"
                width="100%"
                height="100%"
                type="application/pdf"
                style="border: 2px solid #1e293b; border-radius: 8px;"
            ></iframe>
        </div>
        """
        st.markdown(pdf_display, unsafe_allow_html=True)

        st.info("💡 If the PDF doesn't display above, use the download button to view it locally.")

    with view_tab2:
        st.markdown("""
        ### Research Paper Details

        **Title:** Applications of higher order Markov models and Pressure Index to strategize controlled run chases in Twenty20 cricket

        **Authors:**
        - Rhitankar Bandyopadhyay
        - Dibyojyoti Bhattacharjee

        **Year:** 2025

        **Abstract:**
        This study presents a comprehensive framework for quantifying and analyzing pressure in T20 cricket run chases.
        Building upon the foundational work by H.H Lemmer and Dibyojyoti Bhattacharjee (2016), we introduce:

        - **Phase-wise Third Order Markov Models**: Advanced statistical models that capture ball-by-ball dynamics across different match phases (powerplay, middle overs, death overs)
        - **Gamma Distribution Fallbacks**: Robust handling of rare scenarios and edge cases
        - **Strategic Insights**: Data-driven recommendations for controlled run chases

        The Pressure Index (PI) provides a ball-by-ball metric that quantifies the pressure experienced by the batting team,
        enabling teams to make informed strategic decisions during run chases.

        **Key Contributions:**
        - Novel application of higher-order Markov models to cricket analytics
        - Comprehensive analysis of 1000+ T20 matches
        - Practical strategic recommendations for teams and analysts
        - Interactive visualization tools for real-time match analysis
        """)

        st.markdown("---")
        st.markdown("**Citation:** Bandyopadhyay, R., & Bhattacharjee, D. (2025). Applications of higher order Markov models and Pressure Index to strategize controlled run chases in Twenty20 cricket.")


def render_how_it_works():
    """Render the How It Works page"""

    st.markdown("""
    Pressure Index (PI) is a ball-by-ball metric designed to quantify the pressure experienced
    by a team while batting second in a limited-overs cricket match. Based on the foundation laid
    by H.H Lemmer and Dibyojyoti Bhattacharjee (2016) and several subsequent extended works over
    the years, the current study by Rhitankar Bandyopadhyay and Dibyojyoti Bhattacharjee (2025)
    focuses on phasewise third order Markov models and Gamma distribution fallbacks to strategize
    controlled run chases in T20 cricket.

    **Read the full research paper below:**
    """)

    st.markdown("---")

    # PDF Display
    # Get the path to the PDF file (should be in the 'data' folder)
    base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    pdf_path = os.path.join(base_path, 'data', 'Applications_of_higher_order_Markov_models_and_Pressure_Index_to_strategize_controlled_run_chases_in_Twenty20_cricket.pdf')

    # Display the PDF
    display_pdf(pdf_path)


if __name__ == "__main__":
    render_how_it_works()
