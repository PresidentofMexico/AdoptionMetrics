import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from Home import load_and_process_data
from src.metrics import MetricsEngine

st.set_page_config(page_title="ROI & Contract Strategy", page_icon="💎", layout="wide")

try:
    df, _, _ = load_and_process_data()
    if df.empty: st.warning("No data found."); st.stop()
except Exception as e:
    st.error(f"Error: {e}"); st.stop()

st.title("💎 ROI & Contract Strategy")

# --- TABS ---
tab_contract, tab_roi = st.tabs(["⚖️ Contract Optimizer", "💰 Net Value Analysis"])

# ==============================================================================
# TAB 1: CONTRACT OPTIMIZER (BlueFlame Specific)
# ==============================================================================
with tab_contract:
    st.markdown("### BlueFlame License Modeling")
    st.caption("Analyze the break-even point between 'Per Seat' vs 'Unlimited' licensing based on current adoption.")

    # 1. Get Real Data
    # Filter for BlueFlame only for this analysis
    bf_df = df[df['Tool'] == 'BlueFlame']
    current_active_users = bf_df['Email'].nunique()
    
    # 2. Define Models (Based on your Word Doc)
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("**Model Assumptions**")
        base_seats = st.number_input("Base Seat Cap", value=100)
        base_cost = st.number_input("Base Cost ($)", value=250000)
        seat_price = st.number_input("Overage Price/Seat ($)", value=1500)
        unlimited_price = st.number_input("Unlimited Proposal ($)", value=415000)
        service_fee = st.number_input("Service Recapture Fee ($)", value=96000, help="Potential penalty/fee if unlimited isn't taken")
        
    with col2:
        # 3. The Math
        # Generate a range of users from 50 to 300 to show the curve
        x_users = list(range(50, 350, 5))
        
        y_per_seat = []
        y_unlimited = []
        
        for u in x_users:
            # Per Seat Logic: Base + (Max(0, Users - 100) * 1500)
            overage = max(0, u - base_seats)
            cost = base_cost + (overage * seat_price)
            y_per_seat.append(cost)
            
            # Unlimited Logic: Flat Rate
            y_unlimited.append(unlimited_price)
            
        # Create Visualization
        fig = go.Figure()
        
        # Line 1: Per Seat
        fig.add_trace(go.Scatter(x=x_users, y=y_per_seat, mode='lines', name='Current (Per Seat)', line=dict(color='#EF4444', width=3)))
        # Line 2: Unlimited
        fig.add_trace(go.Scatter(x=x_users, y=y_unlimited, mode='lines', name='Unlimited Proposal', line=dict(color='#10B981', width=3, dash='dash')))
        
        # Vertical Line: Current Usage
        fig.add_vline(x=current_active_users, line_dash="dot", annotation_text=f"Current: {current_active_users}", annotation_position="top right", line_color="blue")
        
        # Vertical Line: Break Even
        # Break even is where Base + (X - 100)*1500 = Unlimited
        # (415000 - 250000) / 1500 + 100 = 210
        break_even = (unlimited_price - base_cost) / seat_price + base_seats
        fig.add_vline(x=break_even, line_dash="dot", annotation_text=f"Break-Even: {int(break_even)}", annotation_position="bottom right", line_color="gray")

        fig.update_layout(title="Cost Curve: Per Seat vs Unlimited", xaxis_title="Number of Users", yaxis_title="Annual Cost ($)", height=400)
        st.plotly_chart(fig, use_container_width=True)

    # 4. Strategic Recommendation
    st.divider()
    
    # Calculate current costs
    current_cost_real = base_cost + (max(0, current_active_users - base_seats) * seat_price)
    gap_to_breakeven = int(break_even - current_active_users)
    
    c1, c2, c3 = st.columns(3)
    
    c1.metric("Current Active Users", current_active_users)
    c2.metric("Projected Cost (Current Model)", f"${current_cost_real:,.0f}")
    c3.metric("Unlimited Cost", f"${unlimited_price:,.0f}", delta=f"${unlimited_price - current_cost_real:,.0f} More Expensive", delta_color="inverse")

    if current_active_users < break_even:
        st.info(f"💡 **Recommendation:** Stay on the Per-Seat model. You need to add **{gap_to_breakeven} more users** before the Unlimited plan becomes cheaper.")
        
        if service_fee > 0:
            st.warning(f"⚠️ **Negotiation Point:** If you reject Unlimited, they may charge the **${service_fee:,.0f}** Service Recapture fee. Factor this into your decision.")
    else:
        st.success("✅ **Recommendation:** Switch to Unlimited. You have crossed the break-even threshold.")

# ==============================================================================
# TAB 2: NET ROI ANALYSIS (Existing Logic)
# ==============================================================================
with tab_roi:
    # --- 1. COST INPUTS (Global) ---
    with st.expander("💸 Monthly Cost Basis", expanded=False):
        c1, c2 = st.columns(2)
        # Use the calculated BlueFlame cost from Tab 1
        bf_cost_mo = current_cost_real / 12
        gpt_cost_mo = c2.number_input("ChatGPT Annual ($)", value=120000, step=10000) / 12
        
        tool_costs = {'BlueFlame': bf_cost_mo, 'ChatGPT': gpt_cost_mo}
        st.caption(f"BlueFlame cost dynamic based on {current_active_users} users.")

    # --- 2. ASSUMPTIONS ---
    with st.expander("🧮 Value Assumptions", expanded=True):
        c1, c2, c3, c4 = st.columns(4)
        hourly_rate = c1.number_input("Avg Hourly Cost ($)", value=125)
        discount_rate = c2.slider("Discount Factor (%)", 0, 90, 50) / 100
        
        assumptions = {
            'Standard Chat': 5, 'ChatGPT Messages': 5,
            'Investment Research': 15, 'BlueFlame Messages': 15,
            'Advanced Data Analysis': 30, 'Tool Messages': 30
        }

    # --- 3. CALCULATIONS ---
    engine = MetricsEngine(df)
    roi_df = engine.calculate_roi(hourly_rate, assumptions, discount_rate)
    net_impact = engine.calculate_net_impact(tool_costs)

    # --- 4. KPI DISPLAY ---
    total_gross = roi_df['Dollar_Value'].sum()
    total_cost = sum(tool_costs.values())
    total_net = total_gross - total_cost
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Gross Value (Mo)", f"${total_gross:,.0f}")
    k2.metric("Total Cost (Mo)", f"${total_cost:,.0f}")
    k3.metric("Net Value", f"${total_net:,.0f}", delta_color="normal" if total_net > 0 else "inverse")
    k4.metric("Break-Even Users", int(break_even), help="For BlueFlame Contract")

    st.divider()

    # --- 5. TOOL P
