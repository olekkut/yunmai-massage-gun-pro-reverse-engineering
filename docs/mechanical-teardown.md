# Mechanical Teardown & Percussion Assembly Walkthrough

This engineering guide documents the complete mechanical teardown, structural enclosure disassembly, reciprocating transmission mechanism, and bearing assemblies of the **Yunmai Massage Gun Pro (Model YMFG-B563)**.

---

## Table of Contents
1. [Teardown Tools & Preparation](#1-teardown-tools--preparation)
2. [Step 1: Base Cap & Handle Battery Extraction](#2-step-1-base-cap--handle-battery-extraction)
3. [Step 2: Outer Enclosure & Chassis Separation](#3-step-2-outer-enclosure--chassis-separation)
4. [Step 3: Internal Chassis Frame Bracket](#4-step-3-internal-chassis-frame-bracket)
5. [Step 4: Reciprocating Percussion Transmission Mechanism](#5-step-4-reciprocating-percussion-transmission-mechanism)
6. [Step 5: Piston, Cylinder Sleeve & Linear Guide](#6-step-5-piston-cylinder-sleeve--linear-guide)
7. [Step 6: Brushless Motor Mounting & Housing](#7-step-6-brushless-motor-mounting--housing)
8. [Device Rating Plate & Model Identification](#8-device-rating-plate--model-identification)

---

## 1. Teardown Tools & Preparation

To disassemble the device without damaging the molded ABS/polycarbonate housing:
- **Precision Screwdriver**: Phillips #0 and #1 bits, Torx T8/T10 bits.
- **Nylon Spudger / Prying Tool**: For separating snap-fit seams without marring exterior surfaces.
- **Tweezers**: For disconnecting wire harness locking tabs.
- **Safety Precaution**: Ensure the bottom power rocker switch is in the **OFF (O)** position before teardown.

---

## 2. Step 1: Base Cap & Handle Battery Extraction

Disassembly begins at the base of the handle where power input and primary switching reside:
1. Pry off the decorative rubber base ring to access the base retention screws.
2. Remove the retaining screws securing the bottom end-cap.
3. The base cavity houses the **coaxial DC charging barrel receptacle** and the **heavy-duty rocker power switch**.

![Power Switch and DC Jack Cavity](../hardware/photos/teardown/10_power_switch_dc_jack_cavity.jpg)
*Figure 1: Handle base cavity revealing the power rocker switch and DC charging port mounts.*

4. Gently slide the cylindrical **JETECH 6S lithium-ion battery pack** downward out of the hollow handle chamber.
5. Disconnect the polarized 2-pin power plug from connector `CN1` leading to the motherboard.

![Handle Battery Cavity](../hardware/photos/teardown/09_handle_battery_cavity.jpg)
*Figure 2: Interior view of the handle cavity showing the battery alignment ribs and cable routing channel.*

---

## 3. Step 2: Outer Enclosure & Chassis Separation

1. Unscrew the perimeter screws located under the decorative accent rings.
2. Use a nylon spudger to separate the left and right clamshell halves of the main body.
3. The housing is molded from high-impact ABS/PC polymer with reinforced internal ribbing to absorb acoustic vibrations and high-amplitude mechanical shock.

![Outer Shell Interior](../hardware/photos/teardown/01_outer_shell_interior.jpg)
*Figure 3: Inside face of the outer clamshell enclosure showing motor alignment seats and acoustic dampening ribs.*

---

## 4. Step 3: Internal Chassis Frame Bracket

Inside the plastic enclosure sits a rigid internal chassis frame bracket:
- Manufactured from die-cast aluminum alloy with high torsional rigidity.
- Serves as the central mechanical backbone supporting the BLDC motor, eccentric crankshaft, and reciprocating piston guide.
- Isolated from the outer shell by molded elastomeric silicone dampers to prevent percussion recoil from vibrating into the user's hand.

![Internal Chassis Bracket](../hardware/photos/teardown/02_internal_chassis_bracket.jpg)
*Figure 4: Die-cast aluminum internal chassis bracket holding the motor and percussion transmission.*

---

## 5. Step 4: Reciprocating Percussion Transmission Mechanism

The device converts rotary torque from the brushless motor into high-force linear percussion via a classic **eccentric crank-slider transmission**.

![Reciprocating Mechanism Overview](../hardware/photos/teardown/03_reciprocating_mechanism_overview.jpg)
*Figure 5: Overview of the reciprocating transmission mechanism, eccentric counterweight, and connecting rod.*

### Key Components of the Drive Train
1. **Flywheel Counterweight**: Mounted directly to the motor output shaft. An eccentric mass counterbalances the reciprocating piston mass, minimizing user hand fatigue.
2. **Crank Pin**: Offset from the motor shaft axis by approximately $5.5\text{–}6.0\,\text{mm}$, generating a total reciprocating peak-to-peak stroke length of **$11\text{–}12\,\text{mm}$**.
3. **Connecting Rod (Conrod)**: Machined aluminum connecting rod linking the crank pin to the wrist pin of the percussion piston.
4. **Precision Ball Bearings**:
   - The crank journal and wrist pin are fitted with **Singapore NMB 608Z shielded miniature ball bearings**.
   - These high-speed, deep-groove ball bearings withstand continuous radial loads at up to 3,200 RPM while minimizing friction and thermal buildup.

![Connecting Rod Bearing Detail](../hardware/photos/teardown/04_connecting_rod_bearing_detail.jpg)
*Figure 6: Macro detail of the connecting rod showing the precision Singapore NMB shielded ball bearing.*

---

## 6. Step 5: Piston, Cylinder Sleeve & Linear Guide

1. The front end of the connecting rod pivots on a hardened steel cross-pin inside the reciprocating piston.
2. The piston slides linearly within an extruded self-lubricating cylinder sleeve.
3. The front tip features an internal quick-lock spring detent socket accepting 19 mm shaft massage head attachments (round ball, flat head, bullet head, and U-shaped spinal fork).

![Piston Cylinder Assembly](../hardware/photos/teardown/05_piston_cylinder_assembly.jpg)
*Figure 7: Linear piston cylinder assembly and front attachment mounting socket.*

### Motion Kinematics
For a crank radius $r \approx 6.0\,\text{mm}$ and connecting rod length $L \approx 36.0\,\text{mm}$, the piston displacement $x(\theta)$ as a function of crank angle $\theta$ follows the slider-crank equation:
$$x(\theta) = r \left(1 - \cos\theta + \frac{\lambda}{2}\sin^2\theta\right)$$
Where $\lambda = \frac{r}{L} \approx \frac{6}{36} = 0.167$.

At 3,200 RPM (Gear 3, $53.3\,\text{Hz}$), the piston accelerates up to approximately $200\,\text{m/s}^2$ at top dead center, delivering the deep percussive tissue penetration characteristic of the Yunmai Pro.

---

## 7. Step 6: Brushless Motor Mounting & Housing

The motor is clamped into the internal chassis bracket using four machine screws securing the front faceplate and rear retention plate:

![Motor Mounting Bearing Harness](../hardware/photos/teardown/06_motor_mounting_bearing_harness.jpg)
*Figure 8: Motor front faceplate mounting showing wire harness routing and shaft bearing.*

![Motor Backplate Mounting](../hardware/photos/teardown/07_motor_backplate_mounting.jpg)
*Figure 9: Rear motor backplate mounting securing the motor inside the chassis.*

---

## 8. Device Rating Plate & Model Identification

Located on the underside of the device near the handle joint:
- **Manufacturer**: Shenzhen Yunmai Technology Co., Ltd.
- **Model Number**: **YMFG-B563**
- **Rated Input**: **26.0V DC == 1.0A**
- **Battery**: Rechargeable Lithium-ion Battery Pack
- **Compliance Markings**: CE, RoHS, WEEE recycling symbol.

![Device Rating Plate YMFG-B563](../hardware/photos/teardown/08_device_rating_plate_ymfg_b563.jpg)
*Figure 10: Macro photograph of the Yunmai Massage Gun Pro model rating plate.*
