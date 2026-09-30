"""
AAP Coach Card Data — revised set.
Core measurement testing games (4 families) + all programme games.
Sport-specific testing games removed for now. Split Step removed (to be recreated).
"""

ALL_CARDS = [

# ══════════════════════════════════════════════════════════════════════════════
#  TESTING GAME CARDS — CORE FOUR FAMILIES
# ══════════════════════════════════════════════════════════════════════════════

# ── BALANCE & PROPRIOCEPTION ───────────────────────────────────────────────────

{
    'slug': 'balance-catching',
    'title': 'Balance Catching',
    'badge': 'TESTING GAME',
    'sport': '',
    'equipment': 'Balance Ball / Large Ball',
    'measurement': '1 min per attempt  |  Individual athlete  |  Score = successful catches',
    'task': [
        'Athlete stands on a Balance Ball 2.5 metres from a wall or rebounder.',
        'Within a 1-minute window, the athlete self-rebounds the ball off the wall and attempts to catch it.',
        'Key rule — score a point for each successful catch.',
        'Key rule — athlete must remain on the balance equipment throughout.',
        'Athlete partner to record score.',
    ],
    'environment': (
        'WALL / REBOUNDER — athlete stands on balance implement (Balance Ball) 2.5 metres from wall. '
        'Blue = throw to wall · Orange = rebound catch · 2.5 metres from wall.'
    ),
    'sc_perspective': [
        'Unilateral and bilateral balance under continuous perturbation — balance surface challenges ankle, knee and hip stabilisers through every catch cycle.',
        'Proprioceptive loading — the unstable surface constantly updates postural information, demanding active recalibration.',
        'Kinetic chain activation — core engagement through the throw and catch sequence while maintaining stance on an unstable base.',
    ],
    'cla_perspective': [
        'Perception-action coupling — throw timing is continuously coupled to postural sway; the athlete must feel the surface and see the ball as one integrated action.',
        'Postural attunement — the balance implement creates a rich information environment that reveals and refines the athlete\'s postural control solutions.',
        'Self-organisation — no prescribed catching technique; athletes discover their own stable movement solutions under environmental constraint.',
    ],
    'coach_considerations': [
        'Can adjust distance and ball size as needed.',
        'Make sure athletes have a partner to record scores.',
        'Each testing session must replicate the same set-up (distance, equipment, ball type).',
        'It is not compulsory to use all test options — choose what best fits.',
    ],
    'levels': {
        'L1': '2.5 metres from wall / rebounder · Large ball',
        'L2': '3.5 metres from wall / rebounder · Large ball',
        'L3': '5 metres from wall / rebounder · Large ball',
        'L4': '5 metres · One hand throw & catch · Small ball',
        'L5': '5 metres · Non-dominant hand throw & catch · Small ball',
    },
    'measurement_tests': ['Balance Catching — Large Ball', 'Balance Catching — Small Ball (L4/L5)'],
    'alignment_label': 'MEASUREMENT TESTS THAT ALIGN',
    'tags': {
        'D1': ['Balance & Postural Control'],
        'D2': ['Bilateral Balance', 'Unilateral Balance', 'Proprioception', 'Hand-Eye Coordination'],
        'D3': ['Perception-Action Coupling', 'Postural Attunement', 'Self-Organisation', 'Repetition Without Repetition'],
        'D4': ['Alternating'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Bosu / Balance Ball', 'Large Ball', 'Small Ball', 'Wall'],
        'D7': ['Minimal <5m×5m'],
        'D8': ['Individual'],
        'D9': ['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5'],
        'D10': ['Balance Catching'],
    },
},

{
    'slug': 'lob-scotch',
    'title': 'Lob Scotch',
    'badge': 'TESTING GAME',
    'sport': '',
    'equipment': 'Dots or Cones / Balls',
    'measurement': 'Individual athlete  |  Score = number of squares claimed',
    'task': [
        'Set up the Lob Scotch grid on the floor — 12 squares in a straight pattern: right-foot single, left-foot single, two-foot pair (×3 cycles).',
        'Athlete stands at Start, lobs the ball upward and hops forward to claim the first square, catching the ball on landing.',
        'Athlete returns to Start. Next lob — hop through square 1, hop into square 2, catch. Continue progressing.',
        'At each two-foot pair: leap forward and land with one foot in each square, catching the ball.',
        'Key rule — throw from Start each time. A square is claimed only if the athlete lands correctly and catches the ball.',
        'Key rule — score = total number of squares successfully claimed.',
    ],
    'environment': (
        'Straight pattern on the floor: 3 cycles of R single → L single → two-foot pair (12 squares total). '
        'Blue = right-foot hop · Pink = left-foot hop · Gold = two-foot landing pair. '
        'Athlete lobs from Start and progresses up the grid.'
    ),
    'sc_perspective': [
        'Unilateral balance — single-leg hopping engages core and ankle stabilisers in a progressive sequential pattern.',
        'Rhythmic coordination — alternating one-foot hops and two-foot landings through the grid develops lower-body timing.',
        'Hand-eye coordination — self-fed lob with spatial timing demands accurate vertical throw calibration at each stage.',
    ],
    'cla_perspective': [
        'Perception-action coupling — lob height and hop distance must be continuously coupled to the grid squares; the throw shapes the movement.',
        'Postural attunement — unilateral hopping demands constant proprioceptive adjustment to maintain balance between lob and catch.',
        'Self-organisation — athlete discovers their personal lob-hop-catch coordination pattern without prescribed technique.',
    ],
    'coach_considerations': [
        'Single squares require a one-footed hop; double squares require a two-footed landing. Incorrect foot placement = attempt does not count.',
        'Encourage athletes to track the ball from the moment it leaves their hand — this develops perception-action coupling and spatial judgement.',
        'Keep square size consistent across sessions.',
    ],
    'levels': {
        'L1': 'Straight pattern · 12 squares · Target: 6 claimed',
        'L2': 'Straight pattern · 12 squares · Target: 9 claimed',
        'L3': 'Straight pattern · 12 squares · Target: 12 (all)',
        'L4': 'Zig-zag alternating pattern · 12 squares · Target: 6',
        'L5': 'Zig-zag alternating pattern · 12 squares · Target: 9',
    },
    'measurement_tests': ['Squares Claimed (straight)', 'Squares Claimed (zig-zag — L4+)'],
    'alignment_label': 'MEASUREMENT TESTS THAT ALIGN',
    'tags': {
        'D1': ['Balance & Postural Control'],
        'D2': ['Unilateral Balance', 'Rhythmic Coordination', 'Hand-Eye Coordination', 'Proprioception'],
        'D3': ['Perception-Action Coupling', 'Postural Attunement', 'Self-Organisation', 'Repetition Without Repetition'],
        'D4': ['Unilateral', 'Alternating'],
        'D5': ['Task'],
        'D6': ['Small Ball', 'Gate / Cone'],
        'D7': ['Minimal <5m×5m'],
        'D8': ['Individual'],
        'D9': ['Level 1', 'Level 2'],
        'D10': ['Balance Catching'],
    },
},

{
    'slug': 'lob-scotch-l4',
    'title': 'Lob Scotch — L4 / L5',
    'badge': 'TESTING GAME',
    'sport': '',
    'equipment': 'Dots or Cones / Balls',
    'measurement': 'Individual athlete  |  Score = number of squares claimed',
    'task': [
        'Set up the zig-zag grid: 3 cycles of single (right offset) → single (left offset) → two-foot pair (centre) = 12 squares.',
        'Athlete lobs from Start, hops on the same foot to the first square (right offset), catching on landing.',
        'Return to Start. Same-foot hop to sq 1 (right offset), same-foot hop to sq 2 (left offset), catch, then leap the two-foot pair.',
        'Key rule — same foot to both single squares. No foot alternation. Throw from Start each time.',
        'Key rule — score = squares claimed. L4 target: 6. L5 target: 9.',
    ],
    'environment': (
        'Zig-zag pattern: 3 cycles of same-foot hop (offset right) → same-foot hop (offset left) → two-foot centre pair (12 squares total). '
        'Blue = same-foot hop · Gold = two-foot landing pair. '
        'Athlete lobs from Start and progresses through the zig-zag pattern.'
    ),
    'sc_perspective': [
        'Unilateral lateral loading — hopping on the same foot to offset squares demands sustained single-leg control across a lateral plane.',
        'Rhythmic coordination — the zig-zag pattern requires recalibration of lob direction for each square, elevating the coordination demand over the straight version.',
        'Multi-plane balance — lateral displacement on a single stance leg challenges frontal and sagittal plane stability simultaneously.',
    ],
    'cla_perspective': [
        'Increased affordance complexity — the zig-zag grid creates directional variability that demands more continuous perceptual reading of space.',
        'Perception-action coupling — the lob must be directed slightly left or right for each square; throw direction and hop are coupled to a more dynamic spatial target.',
        'Self-organisation — athletes discover new coordination solutions for same-foot lateral hopping without prescribed technique.',
    ],
    'coach_considerations': [
        'Ensure athletes understand the zig-zag pattern before starting — right-foot squares are offset to the right, left-foot squares to the left.',
        'The two-foot pair returns to centre — this is the reset point for each cycle.',
        'Keep square size consistent with L1–L3 assessment so scores are comparable.',
    ],
    'levels': {
        'L4': 'Zig-zag alternating pattern · 12 squares · Target: 6 claimed',
        'L5': 'Zig-zag alternating pattern · 12 squares · Target: 9 claimed',
    },
    'measurement_tests': ['Squares Claimed (zig-zag — L4+)'],
    'alignment_label': 'MEASUREMENT TESTS THAT ALIGN',
    'tags': {
        'D1': ['Balance & Postural Control'],
        'D2': ['Unilateral Balance', 'Rhythmic Coordination', 'Hand-Eye Coordination', 'Lateral Loading'],
        'D3': ['Perception-Action Coupling', 'Postural Attunement', 'Self-Organisation'],
        'D4': ['Unilateral', 'Alternating'],
        'D5': ['Task'],
        'D6': ['Small Ball', 'Gate / Cone'],
        'D7': ['Minimal <5m×5m'],
        'D8': ['Individual'],
        'D9': ['Level 4', 'Level 5'],
        'D10': ['Lob Scotch'],
    },
},

{
    'slug': 'lob-scotch-partner-feed',
    'title': 'Lob Scotch — Partner Feed',
    'badge': 'PROGRAMME GAME',
    'sport': '',
    'equipment': 'Dots or Cones / Balls',
    'measurement': '1 min  |  Pairs (swap roles)  |  Score = squares claimed',
    'task': [
        'Set up the Lob Scotch grid on the floor — 12 squares: right-foot single, left-foot single, two-foot pair (×3 cycles). Mark a feed cone 2.5 metres away.',
        'Athlete starts at the beginning of the grid. Partner stands at the feed cone(s) with the ball.',
        'On GO, athlete hops progressively through the grid — single squares on one foot, two-foot pairs with a leap. Partner feeds the ball to the athlete at each square.',
        'Key rule — a square is claimed only if the athlete lands correctly AND catches the partner\'s feed. Score 1 point per square claimed.',
        'Key rule — if the catch is missed, the athlete does not score that square but continues hopping through the grid. Reset to Start and repeat.',
        'After 1 minute, swap roles. Highest score wins the round.',
    ],
    'environment': (
        'Straight grid on the floor: 3 cycles of R single → L single → two-foot pair (12 squares). '
        'Feed cone(s) positioned 2.5m away — front, either side, or combination. '
        'Athlete hops through grid; partner feeds at each landing.'
    ),
    'sc_perspective': [
        'Unilateral balance — single-leg hopping while tracking and catching a live partner feed elevates the postural demand beyond the self-lob version.',
        'Rhythmic coordination — the athlete must synchronise hop timing and catch timing to an externally controlled feed, introducing a new inter-personal timing demand.',
        'Hand-eye coordination under locomotion — catching at the point of landing from a partner requires the athlete to read an external ball flight mid-hop.',
    ],
    'cla_perspective': [
        'Perception-action coupling — the athlete must couple hop direction, landing position and catching action to a partner\'s throw rather than their own self-generated lob; this fundamentally changes the information structure.',
        'Interpersonal coordination — both athlete and feeder must co-regulate timing and throw weight across the minute; the partnership develops its own rhythm.',
        'Self-organisation — feeding position and throw angle vary progressively; athlete discovers new catching solutions across different approach angles without coaching.',
    ],
    'coach_considerations': [
        'Feeder should aim for the athlete\'s landing zone — reward consistent feeding as much as hopping quality.',
        'Front feed is the starting position; side feeds add directional catching demands once the base pattern is established.',
        'Encourage feeders to vary height and weight slightly — this sharpens the athlete\'s perception-action coupling.',
        'Use combination feeds (front + both sides in one round) to maximise unpredictability and cognitive load.',
    ],
    'levels': {
        'L1': 'Straight grid · Feed from front · 2.5 metres · 1 minute',
        'L2': 'Straight grid · Feed from either side · 2.5 metres · 1 minute',
        'L3': 'Straight grid · Combination (front + sides) · 2.5 metres · 1 minute',
        'L4': 'Straight grid · Combination · 5 metres · 1 minute',
        'L5': 'Zig-zag grid (L4/L5 pattern) · Combination · 10 metres · 1 minute',
    },
    'tags': {
        'D1': ['Balance & Postural Control'],
        'D2': ['Unilateral Balance', 'Rhythmic Coordination', 'Hand-Eye Coordination', 'Proprioception'],
        'D3': ['Perception-Action Coupling', 'Postural Attunement', 'Self-Organisation', 'Interpersonal Coordination'],
        'D4': ['Unilateral', 'Alternating'],
        'D6': ['Small Ball', 'Large Ball', 'Gate / Cone'],
        'D7': ['Minimal <5m×5m'],
        'D8': ['Pair'],
        'D9': ['Level 1', 'Level 2', 'Level 3'],
        'D10': ['Lob Scotch'],
    },
},

# ── SPEED & AGILITY ────────────────────────────────────────────────────────────

{
    'slug': 'skipping-rope-relay',
    'title': 'Skipping Rope Sprint Relay',
    'badge': 'PROGRAMME GAME',
    'sport': '',
    'equipment': 'Skipping Ropes / Cones',
    'measurement': 'Pairs relay  |  Timed  |  Score = total relay time',
    'task': [
        'Set up a 25-metre straight course with clear start/finish lines. Each athlete has their own skipping rope.',
        'Athlete A skips the first 25m leg. The moment A crosses the line, Athlete B immediately skips the return leg (25m back). Athletes alternate every 25m from there.',
        'Key rule — no baton; the next athlete triggers the instant their partner crosses the line. Each athlete completes alternating 25m legs throughout the relay.',
        'Key rule — record the total time from Athlete A\'s first step to the final athlete crossing the finish line. Pairs compete against pairs for fastest time.',
        'Run 2–3 timed relay attempts. Best time is the recorded score.',
    ],
    'environment': (
        'START ——25 metres—— FINISH. '
        'Athletes alternate every 25m: A1 to Finish · A2 back to Start · A1 to Finish · and so on. '
        'Each leg = 25m. No baton — next athlete triggers on partner\'s line crossing.'
    ),
    'sc_perspective': [
        'Rhythmic coordination under competitive pressure — the relay format adds urgency and inter-athlete timing to the skipping sprint constraint.',
        'Linear speed — each 25m leg demands the same sprint mechanics adapted around the rope, now with faster pace driven by competitive context.',
        'Plyometric power — rapid ground contact and rope clearance timing maintained across repeated relay legs under progressive fatigue.',
    ],
    'cla_perspective': [
        'Constrain to afford — the rope continues to generate rhythmic movement solutions while the relay structure adds a social timing constraint not present in individual testing.',
        'Interpersonal coordination — pairs develop a shared relay rhythm across attempts; the trigger cue (partner crossing the line) requires continuous attention to the other athlete.',
        'Repetition without repetition — each relay leg is a slightly different coordination challenge as fatigue accumulates and competitive intensity builds.',
    ],
    'coach_considerations': [
        'Teams of 3 are recommended for the 75m option (3 legs of 25m, one each) — pairs doing 75m will have one athlete complete 2 legs vs the other\'s 1.',
        'The 100m square option works well with teams of 4 (one side each at 25m). Pairs can do the square by completing 2 sides each.',
        'The no-baton rule keeps transitions sharp and creates a natural spectator moment at each line crossing.',
        'Run multiple pairs simultaneously in parallel lanes to maximise competitive intensity and comparison.',
    ],
    'levels': {
        'L1': '50m relay · 2 legs of 25m · 1 leg each',
        'L2': '75m relay · 3 legs of 25m · teams of 3 recommended',
        'L3': '100m relay · 4 legs of 25m · 2 legs each (50m each)',
        'L4': '100m square · pairs (2 sides each) or team of 4 (1 side each)',
        'L5': 'Max distance relay · timed 3 minutes · most 25m legs completed',
    },
    'tags': {
        'D1': ['Dynamic Locomotor'],
        'D2': ['Rhythmic Coordination', 'Linear Speed', 'Plyometric Power'],
        'D3': ['Constrain to Afford', 'Interpersonal Coordination', 'Repetition Without Repetition', 'Functional Variability'],
        'D4': ['Bilateral'],
        'D6': ['Standard Rope'],
        'D7': ['Large 15m+'],
        'D8': ['Pair', 'Small Group 3–5'],
        'D9': ['Level 1', 'Level 2', 'Level 3'],
        'D10': ['Skipping Rope Sprint'],
    },
},

{
    'slug': 'skipping-rope-sprint',
    'title': 'Skipping Rope Sprint',
    'badge': 'TESTING GAME',
    'sport': '',
    'equipment': 'Skipping Rope / Cones',
    'measurement': '3 timed trials  |  Individual athlete  |  Score = average time (sec)',
    'task': [
        'Set up a straight line 25-metre course with a clear start and finish line.',
        'Athlete completes the 25m distance running whilst skipping over a rope.',
        'Key rule — each of three trials timed over the full distance.',
        'Key rule — the average of the three times is the recorded score.',
        'Athlete partner or practitioner to record times.',
    ],
    'environment': (
        'START ———25 metres——— FINISH. '
        'Athlete runs 25m whilst skipping over the rope continuously.'
    ),
    'sc_perspective': [
        'Rhythmic coordination — synchronising stride length and rope rotation under sustained locomotion.',
        'Linear speed — sprint mechanics adapted around the rope constraint; gait pattern must remain efficient.',
        'Plyometric power — rapid ground contact times with rope clearance timing create a natural plyometric demand.',
    ],
    'cla_perspective': [
        'Constrain to afford — the rope creates a task constraint that surfaces and develops rhythmic movement solutions athletes would not discover in open sprinting.',
        'Repetition without repetition — each trial presents a slightly different coordination challenge as fatigue and rhythm shift.',
        'Functional variability — the athlete self-organises a unique stride-rope coupling pattern; no two athletes solve it identically.',
    ],
    'coach_considerations': [
        'Can adjust distance if needed (e.g. 50m for advanced athletes).',
        'Make sure athletes have a partner or practitioner to record times.',
        'Each testing session must replicate the same set-up (distance, surface).',
    ],
    'levels': {
        'L1': '25 metres — 1 length',
        'L2': '50 metres — there and back (2 lengths)',
        'L3': '75 metres — 3 lengths',
        'L4': '100 metres — 4 lengths',
        'L5': '100 metre square',
    },
    'measurement_tests': ['Time 1', 'Time 2', 'Time 3', 'Average (auto-calculated)'],
    'alignment_label': 'MEASUREMENT TESTS THAT ALIGN',
    'tags': {
        'D1': ['Dynamic Locomotor'],
        'D2': ['Rhythmic Coordination', 'Linear Speed', 'Plyometric Power'],
        'D3': ['Constrain to Afford', 'Repetition Without Repetition', 'Functional Variability'],
        'D4': ['Bilateral'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Standard Rope'],
        'D7': ['Large 15m+'],
        'D8': ['Individual'],
        'D9': ['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5'],
        'D10': ['Skipping Rope Sprint'],
    },
},

{
    'slug': 'diamond-gates',
    'title': 'Diamond Gates',
    'badge': 'TESTING GAME',
    'sport': '',
    'equipment': 'Cones',
    'measurement': '1 min per attempt  |  Small Group (3/4/5) or Large Group (6/7/8)  |  Score = gates completed',
    'task': [
        'Set up a diamond of 4 gates using cones — 15m×15m. Athletes start from a square in the centre.',
        'On GO, athletes sprint to touch through as many gates as possible in 1 minute.',
        'Key rule — cannot return to the same gate twice in a row.',
        'Key rule — athletes must return to the centre square after each gate.',
        'Athlete partner to record score.',
    ],
    'environment': (
        'Diamond: Gate N, Gate S, Gate W, Gate E — 15m between opposite gates. '
        'Navy square = start/return position. Orange = gates (cone pairs).'
    ),
    'sc_perspective': [
        'Change of direction speed (CODs) — maximal acceleration and deceleration across 15–20m repeated throughout the minute.',
        'Reactive agility — gate selection is made in real time; athletes read available gates and choose without a prescribed sequence.',
        'Horizontal power — first-step explosiveness out of the centre square drives the gate count.',
    ],
    'cla_perspective': [
        'Constrain to potentiate — the no-repeat-gate rule forces continuous direction changes and decisions, creating the agility demand without drilling patterns.',
        'Attunement & calibration — athletes calibrate their movement speed to gate distance across the session.',
        'Functional locomotion — sprint and direction-change patterns emerge from spatial constraint rather than prescribed drill.',
    ],
    'coach_considerations': [
        'Can adjust numbers as needed.',
        'Make sure athletes have a partner to record scores.',
        'Each testing session must replicate the same set-up (distance, athlete numbers).',
        'Not compulsory to use all three test options.',
    ],
    'levels': {
        'L1': 'Grid size 15 metres × 15 metres',
        'L2': 'Grid size 12 metres × 12 metres',
        'L3': 'Grid size 10 metres × 10 metres',
        'L4': 'Grid size 7 metres × 7 metres',
        'L5': 'Grid size 5 metres × 5 metres',
    },
    'measurement_tests': [
        'Running Room (4 participants)',
        'No Spare Gates (5 participants)',
        'Mass Running (6 participants)',
    ],
    'alignment_label': 'MEASUREMENT TESTS THAT ALIGN',
    'tags': {
        'D1': ['Dynamic Locomotor'],
        'D2': ['Change of Direction Speed', 'Reactive Agility', 'Horizontal Power'],
        'D3': ['Constrain to Potentiate', 'Attunement & Calibration', 'Self-Organisation', 'Functional Locomotion'],
        'D4': ['Bilateral'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Gate / Cone'],
        'D7': ['Large 15m+'],
        'D8': ['Small Group 3–5', 'Large Group 6+'],
        'D9': ['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5'],
        'D10': ['Diamond Gates'],
    },
},

{
    'slug': 'diamond-dribble',
    'title': 'Diamond Dribble',
    'badge': 'TESTING GAME',
    'sport': '',
    'equipment': 'Cones / Large Balls',
    'measurement': '1 min per attempt  |  Small Group (3/4/5) or Large Group (6/7/8)  |  Score = gates completed',
    'task': [
        'Set up a diamond of 4 gates using cones — 15m×15m. Athletes start from a square of cones in the centre.',
        'On GO, athletes dribble a ball through as many gates as possible in 1 minute.',
        'Key rule — cannot return to the same gate twice in a row.',
        'Key rule — athletes must return to the centre square after each gate.',
        'Athlete partner to record score.',
    ],
    'environment': (
        'Diamond: Gate N, Gate S, Gate W, Gate E — 15m between opposite gates. '
        'Navy square = start/return position in centre. Orange = gates (cone pairs).'
    ),
    'sc_perspective': [
        'Change of direction speed (CODs) — repeated maximal deceleration and re-acceleration between each gate and the centre square.',
        'Ball manipulation/dribbling — maintaining ball control at speed while executing gate-to-centre-to-gate patterns.',
        'Reactive agility — real-time gate selection under competitive time pressure with no prescribed sequence.',
    ],
    'cla_perspective': [
        'Attunement & calibration — athlete learns the gate spacing and their own dribbling pace to calibrate timing across the diamond.',
        'Self-organisation — gate selection and ball control solutions emerge without instruction through the competitive constraint.',
        'Constrain to potentiate — return-to-centre rule creates the repeated acceleration demand that builds the quality being tested.',
    ],
    'coach_considerations': [
        'Can adjust numbers as needed.',
        'Make sure athletes have a partner to record scores.',
        'Each testing session must replicate the same set-up (distance, athlete numbers).',
        'Not compulsory to use all three test options — choose what best fits.',
    ],
    'levels': {
        'L1': 'Grid size 15 metres × 15 metres',
        'L2': 'Grid size 12 metres × 12 metres',
        'L3': 'Grid size 10 metres × 10 metres',
        'L4': 'Grid size 7 metres × 7 metres',
        'L5': 'Grid size 10 metres × 10 metres · Small ball',
    },
    'measurement_tests': [
        'Dribble Room (4 participants)',
        'No Vacancy (5 participants)',
        'Mass Dribbling (6 participants)',
    ],
    'alignment_label': 'MEASUREMENT TESTS THAT ALIGN',
    'tags': {
        'D1': ['Dynamic Locomotor'],
        'D2': ['Change of Direction Speed', 'Ball Manipulation / Dribbling', 'Reactive Agility'],
        'D3': ['Attunement & Calibration', 'Self-Organisation', 'Constrain to Potentiate'],
        'D4': ['Alternating'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Large Ball', 'Small Ball', 'Gate / Cone'],
        'D7': ['Large 15m+'],
        'D8': ['Small Group 3–5', 'Large Group 6+'],
        'D9': ['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5'],
        'D10': ['Diamond Dribble'],
    },
},

{
    'slug': 'grid-leap-partner-feed',
    'title': 'Grid Leap — Partner Feed',
    'badge': 'PROGRAMME GAME',
    'sport': '',
    'equipment': 'Cones or Dots / Balls',
    'measurement': '1 min  |  Pairs (rotate roles)  |  Score = squares claimed',
    'task': [
        'Set up the Grid Leap pyramid — 14 squares in an inverted pyramid (rows of 2-3-4-5). Place a feed cone 2.5 metres from the take-off point.',
        'Athlete stands behind the take-off cones. Partner stands at the feed cone with the ball.',
        'On GO, athlete leaps continuously toward squares in the pyramid while the partner feeds the ball timed to each landing.',
        'Key rule — a square is claimed only if the athlete lands correctly in it AND catches the partner\'s feed on landing. Score 1 point per square.',
        'Key rule — if the catch is missed, the square is not claimed. Athlete returns to take-off and leaps again. Continue for 1 minute.',
        'Rotate roles after 1 minute. Highest score across both roles wins the round.',
    ],
    'environment': (
        'Inverted pyramid: rows of 2–3–4–5 squares (14 targets). Take-off cones 50 cm from row 1. '
        'Feed cone(s) 2.5m away — front, either side, or combination. '
        'Athlete leaps to any square; partner feeds timed to the landing.'
    ),
    'sc_perspective': [
        'Plyometric power — explosive multi-directional leaping to 14 unique targets across the pyramid, now without the self-generated throw to help regulate jump force and direction.',
        'Landing mechanics — absorbing bilateral or unilateral landing force while simultaneously catching a live partner feed creates a higher reactive demand than the test version.',
        'Hand-eye coordination — catching at the peak of a landing effort from a partner throw introduces an external visual-motor coupling demand.',
    ],
    'cla_perspective': [
        'Perception-action coupling — the athlete must read the partner\'s feed trajectory mid-leap and adjust both catch position and landing simultaneously; these were self-coupled in the test, now they are interpersonally coupled.',
        'Interpersonal coordination — feeder and leaper must co-regulate timing and throw weight across the minute; the shared rhythm becomes the performance variable.',
        'Landscape of affordances — 14 unique squares each invite a different leap solution; varied feed angles (front, side, combination) further multiply the affordance landscape.',
    ],
    'coach_considerations': [
        'Feeder should aim to release just before the athlete leaves the ground — too early and the ball arrives before landing; too late and the athlete is already set.',
        'Encourage feeders to vary height slightly to mirror the challenge of the test\'s self-toss.',
        'Side feeds are significantly harder — they require the athlete to twist mid-air or catch across the body on landing.',
        'Track which squares remain unclaimed — athletes naturally gravitate to easier squares; encourage full pyramid coverage.',
    ],
    'levels': {
        'L1': 'Pyramid · Feed from front · 2.5 metres · 1 minute',
        'L2': 'Pyramid · Feed from either side · 2.5 metres · 1 minute',
        'L3': 'Pyramid · Combination (front + sides) · 2.5 metres · 1 minute',
        'L4': 'Pyramid · Combination · 5 metres · 1 minute',
        'L5': 'Pyramid · Combination · 10 metres · 1 minute',
    },
    'tags': {
        'D1': ['Explosive & Landing'],
        'D2': ['Plyometric Power', 'Landing Mechanics', 'Hand-Eye Coordination'],
        'D3': ['Perception-Action Coupling', 'Self-Organisation', 'Interpersonal Coordination', 'Landscape of Affordances'],
        'D4': ['Bilateral', 'Unilateral'],
        'D6': ['Large Ball', 'Small Ball', 'Gate / Cone'],
        'D7': ['Minimal <5m×5m'],
        'D8': ['Pair'],
        'D9': ['Level 1', 'Level 2', 'Level 3'],
        'D10': ['Grid Leap'],
    },
},

# ── PLYOMETRIC & POWER ─────────────────────────────────────────────────────────

{
    'slug': 'step-up-pairs',
    'title': 'Step Up — Pairs',
    'badge': 'PROGRAMME GAME',
    'sport': '',
    'equipment': 'Large Ball / Bench or Plyometric Step',
    'measurement': '1 min  |  Pairs competition  |  Score = catches on step',
    'task': [
        'Set up a step or bench. Partner stands 2 metres away facing the athlete with the ball.',
        'Within a 1-minute window, the partner feeds the ball to the athlete continuously. The athlete leaps or steps onto the bench to catch each feed.',
        'Key rule — a catch with two feet on the step or bench scores 1 point.',
        'Key rule — athlete must step back off the bench fully before each next leap. Catching without both feet on the bench does not score.',
        'Compete pair vs pair — highest score in the minute wins. Swap roles and repeat.',
    ],
    'environment': (
        'PARTNER — STEP/BENCH — ATHLETE position. Partner stands 2 metres away and feeds. '
        'Blue = feed from partner · Orange = leap onto step and catch. '
        'Athlete steps off between each rep.'
    ),
    'sc_perspective': [
        'Plyometric power — explosive two-footed take-off and landing onto an elevated surface while receiving a live partner feed, removing the self-regulation of the wall rebound.',
        'Landing mechanics — stable bilateral landing on a narrow elevated target while tracking and catching a ball from an externally controlled source.',
        'Reactive balance — the partner\'s feed varies slightly in height, weight and angle each rep, creating an unpredictable reactive demand on landing.',
    ],
    'cla_perspective': [
        'Perception-action coupling — jump timing and height are now coupled to the partner\'s throw rather than a wall rebound; the information source is human and less predictable, elevating the perceptual demand.',
        'Interpersonal coordination — athlete and feeder co-regulate rhythm across the minute; the most effective pairs develop a shared timing loop.',
        'Self-organisation — athlete discovers their optimal leap timing and catch position relative to a live partner without prescribed technique.',
    ],
    'coach_considerations': [
        'Feeder controls the pace — a consistent, well-timed feed creates the best learning environment.',
        'Encourage feeders to vary height and weight slightly once the basic rhythm is established.',
        'Athletes who rush will miss the two-feet-on rule — remind them to land before catching, not catch while landing.',
        'Compete multiple pairs simultaneously for heightened competitive atmosphere.',
    ],
    'levels': {
        'L1': 'Partner 2 metres away · 1 minute',
        'L2': 'Partner 3 metres away · 1 minute',
        'L3': 'Partner 4 metres away · 1 minute',
        'L4': 'Partner 4 metres away · 45 seconds',
        'L5': 'Partner 4 metres away · 30 seconds',
    },
    'tags': {
        'D1': ['Explosive & Landing'],
        'D2': ['Plyometric Power', 'Landing Mechanics', 'Bilateral Balance', 'Proprioception'],
        'D3': ['Perception-Action Coupling', 'Self-Organisation', 'Interpersonal Coordination'],
        'D4': ['Bilateral'],
        'D6': ['Large Ball', 'Small Ball', 'Step / Box'],
        'D7': ['Minimal <5m×5m'],
        'D8': ['Pair'],
        'D9': ['Level 1', 'Level 2', 'Level 3'],
        'D10': ['Step Up'],
    },
},

{
    'slug': 'grid-leap',
    'title': 'Grid Leap',
    'badge': 'TESTING GAME',
    'sport': '',
    'equipment': 'Cones or Dots / Balls',
    'measurement': 'Attempts per variation = number of targets  |  Individual athlete  |  Score = points per attempt',
    'task': [
        'Set up a grid of squares or dots in an inverted pyramid — 2 squares closest to athlete, then 3, 4, then 5.',
        'Athlete must leap from behind a pair of take-off cones, 50 cm from the first targets.',
        'Athlete tosses their ball and leaps from outside the cones and must catch it upon landing.',
        'Objective — catch the ball and land in each square across the pyramid.',
        'Key rule — target claimed by first point of landing.',
        'Key rule — points only scored if ball is also caught.',
    ],
    'environment': (
        'Top-down view: 1m×1m squares in inverted pyramid rows (2–3–4–5). '
        'Athlete approaches from below the 2-square row. '
        'Each square is a unique target — once landed, it cannot be re-scored.'
    ),
    'sc_perspective': [
        'Plyometric power — explosive take-off with directed horizontal and vertical force toward a precise target.',
        'Landing mechanics — single-leg and bilateral landing with simultaneous ball control; absorbing force cleanly on a small target.',
        'Hand-eye coordination — airborne catch timed to the self-tossed ball trajectory under leap constraint.',
    ],
    'cla_perspective': [
        'Perception-action coupling — ball toss trajectory is continuously linked to leap direction and timing; athlete must couple two self-generated actions.',
        'Self-organisation — athlete discovers the optimal leap style (broad jump, step jump, pivot) for each unique square target.',
        'Landscape of affordances — the pyramid structure creates 14–20 different spatial affordances; each square invites a slightly different solution.',
    ],
    'coach_considerations': [
        'Make sure athletes have a partner to record scores.',
        'Squares can be smaller than 1m×1m but a challenge must remain in the design.',
        'Each testing session must replicate the same set-up.',
        'Change distance from grid if important for testing.',
    ],
    'levels': {
        'L1': '14 targets · 50 cm · Score: 9 claimed (rows 1–3)',
        'L2': '14 targets · 50 cm · Score: 14 claimed (full pyramid)',
        'L3': '20 targets (add 6-square row) · 50 cm · Score: TBC',
        'L4': 'Non-dominant take-off · 14 targets · Score: 9 claimed',
        'L5': 'Non-dominant take-off · 14 targets · Score: 14 claimed',
    },
    'measurement_tests': ['Small Ball', 'Large Ball'],
    'alignment_label': 'MEASUREMENT TESTS THAT ALIGN',
    'tags': {
        'D1': ['Explosive & Landing'],
        'D2': ['Plyometric Power', 'Landing Mechanics', 'Hand-Eye Coordination'],
        'D3': ['Perception-Action Coupling', 'Self-Organisation', 'Functional Variability', 'Constrain to Afford'],
        'D4': ['Bilateral', 'Unilateral'],
        'D5': ['Task'],
        'D6': ['Large Ball', 'Small Ball', 'Gate / Cone'],
        'D7': ['Minimal <5m×5m'],
        'D8': ['Individual'],
        'D9': ['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5'],
        'D10': ['Grid Leap'],
    },
},

{
    'slug': 'step-up',
    'title': 'Step Up',
    'badge': 'TESTING GAME',
    'sport': '',
    'equipment': 'Large Ball / Bench or Plyometric Step',
    'measurement': '1 min per attempt  |  Individual athlete  |  Score = catches in 1 minute',
    'task': [
        'Set up a step or bench 2 metres from a wall or rebounder.',
        'Athlete throws the ball against the wall or rebounder.',
        'Athlete leaps or steps onto the step or bench to catch the rebounding ball.',
        'Key rule — a catch with two feet on the step/bench scores a point.',
        'Athlete partner to record score.',
    ],
    'environment': (
        'WALL — STEP/BENCH — ATHLETE position. 2 metres from step to wall. '
        'Blue = throw to wall · Orange = rebound catch on step/bench.'
    ),
    'sc_perspective': [
        'Plyometric power — explosive two-footed take-off and landing onto an elevated surface while receiving a ball.',
        'Landing mechanics — stable bilateral landing on a narrow, elevated target with simultaneous catch.',
        'Balance & proprioception — maintaining postural control on an elevated step/bench immediately after landing.',
    ],
    'cla_perspective': [
        'Perception-action coupling — wall rebound trajectory must be coupled to jump timing and height; all three elements are a single continuous perception-action event.',
        'Self-organisation — athlete discovers their optimal throw height, force and jump coordination without prescribed technique.',
        'Constrain to afford — step creates an elevated landing target that affords exploration of varied jump solutions not present in flat-ground catching.',
    ],
    'coach_considerations': [
        'Make sure athletes have a partner to record scores.',
        'Each testing session must replicate the same set-up.',
        'Change the distance if important for testing.',
    ],
    'levels': {
        'L1': '2 metres from wall · 1 minute',
        'L2': '3 metres from wall · 1 minute',
        'L3': '4 metres from wall · 1 minute',
        'L4': '4 metres from wall · 45 seconds',
        'L5': '4 metres from wall · 30 seconds',
    },
    'measurement_tests': ['Bench Catch', 'Hurdle Leap'],
    'alignment_label': 'MEASUREMENT TESTS THAT ALIGN',
    'tags': {
        'D1': ['Explosive & Landing'],
        'D2': ['Plyometric Power', 'Landing Mechanics', 'Bilateral Balance', 'Proprioception'],
        'D3': ['Perception-Action Coupling', 'Self-Organisation', 'Constrain to Afford'],
        'D4': ['Bilateral'],
        'D5': ['Task'],
        'D6': ['Large Ball', 'Small Ball', 'Step / Box', 'Wall'],
        'D7': ['Minimal <5m×5m'],
        'D8': ['Individual'],
        'D9': ['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5'],
        'D10': ['Step Up'],
    },
},

# ══════════════════════════════════════════════════════════════════════════════
#  PROGRAMME GAME CARDS
# ══════════════════════════════════════════════════════════════════════════════

# ── BALANCE & PROPRIOCEPTION ───────────────────────────────────────────────────

{
    'slug': 'balance-catch-pairs',
    'title': 'Balance Catch — Pairs',
    'badge': 'PROGRAMME GAME',
    'sport': '',
    'equipment': 'Balance Ball / Large Ball',
    'measurement': '1 min  |  Pairs competition  |  Score = successful catches',
    'task': [
        'Pairs stand on their own Balance Ball, 2.5 metres apart, facing each other.',
        'Within a 1-minute window, partners throw to each other and attempt to catch while staying on the balance equipment.',
        'Key rule — score 1 point for each successful catch received.',
        'Key rule — both athletes must remain on their balance equipment throughout. Stepping off = catch does not score.',
        'Compete pair vs pair — highest combined score wins the round.',
    ],
    'environment': (
        'PAIRS — athletes stand on a Balance Ball 2.5 metres apart. '
        'Blue = throw to partner · Orange = receive and catch. '
        'Both athletes on balance equipment simultaneously.'
    ),
    'sc_perspective': [
        'Unilateral and bilateral balance under perturbation — receiving a live throw from a partner creates unpredictable force demands on the balance surface, elevating the proprioceptive challenge beyond the wall-bounce version.',
        'Kinetic chain activation — throwing and catching to a partner requires active postural recalibration through every exchange cycle.',
        'Reactive balance — the athlete must absorb catch force while maintaining stance on an unstable surface; the live partner adds variability in throw height, weight and angle.',
    ],
    'cla_perspective': [
        'Perception-action coupling — throw timing, trajectory, and postural response are coupled to the partner\'s movement and the surface simultaneously.',
        'Interpersonal coordination — two athletes on unstable surfaces create a shared, co-regulating information environment; each throw adapts to the partner\'s postural state.',
        'Self-organisation — pairs discover their own throwing rhythm and force calibration without coaching; the balance surface constrains and reveals solutions naturally.',
    ],
    'coach_considerations': [
        'Start at 2.5 metres — pairs can adjust distance to manage difficulty.',
        'Encourage athletes to communicate before the round to establish a throwing rhythm.',
        'Each session must replicate the same distance and equipment type for valid comparisons.',
        'Compete multiple pairs simultaneously for heightened competitive atmosphere.',
    ],
    'levels': {
        'L1': '2.5 metres apart · Large ball · 1 minute',
        'L2': '3.5 metres apart · Large ball · 1 minute',
        'L3': '5 metres apart · Large ball · 1 minute',
        'L4': '5 metres · One hand throw & catch · Small ball',
        'L5': '5 metres · Non-dominant hand throw & catch · Small ball',
    },
    'tags': {
        'D1': ['Balance & Postural Control'],
        'D2': ['Bilateral Balance', 'Unilateral Balance', 'Proprioception', 'Hand-Eye Coordination'],
        'D3': ['Perception-Action Coupling', 'Postural Attunement', 'Self-Organisation', 'Interpersonal Coordination'],
        'D4': ['Alternating'],
        'D6': ['Bosu / Balance Ball', 'Large Ball', 'Small Ball'],
        'D7': ['Minimal <5m×5m'],
        'D8': ['Pair'],
        'D9': ['Level 1', 'Level 2', 'Level 3'],
        'D10': ['Balance Catching'],
    },
},

{
    'slug': 'diamond-gates-teams',
    'title': 'Diamond Gates Teams',
    'badge': 'PROGRAMME GAME',
    'sport': '',
    'equipment': 'Large Ball / Gate / Cone',
    'measurement': '2v2 or 3v3  |  One ball  |  Timed or first to a set score',
    'task': [
        'Set up the diamond — 4 gates at each corner, centre square marked. Two teams of 2–3 players share one ball and compete in the same space.',
        'Teams score by moving the ball through any gate — either dribbling through it or passing through so a teammate catches on the other side. Both methods score 1 point.',
        'Key rule — a team cannot score in the same gate twice in a row. They must score through a different gate before returning to score through the same one.',
        'Teams can pass, carry or dribble anywhere in the playing area to create an opportunity at any gate.',
        'Double-point gates (optional, coach or athlete-regulated) — designate one or two gates as worth 2 points. Teams and coaches can choose which gates are double-point before or during the game.',
        'Gate-guarding rule (coach decides) — by default, teams cannot stand inside or block a gate. For a more strategic variant, allow one player per team to guard any gate they choose.',
        'Play timed (2 minutes per round) or first to a target score (e.g. 10 points). Rotate team composition and restart.',
    ],
    'environment': (
        'Diamond: 4 gates at each corner + centre square. 2 teams share the space with 1 ball. '
        'Score by dribbling or passing through any gate (teammate catches). '
        'No same-gate repeat in a row. Optional: 1–2 gates worth double. '
        'Coach sets gate-guarding rule: open (default) or one-player-per-gate allowed.'
    ),
    'sc_perspective': [
        'Change of direction speed (CODs) — continuous reorientation between gate positions under pressure from an opposition creates genuine reactive COD demands with a ball.',
        'Reactive agility — decisions about which gate to attack are coupled to real-time opponent positioning, not predictable patterns; athletes must read, decide and move simultaneously.',
        'Acceleration and deceleration — exploiting space to reach a gate before the defence closes down requires explosive short-burst acceleration out of transitions.',
        'Ball control under pressure — both dribbling through a gate and receiving a pass cleanly while moving require coordinated footwork and hand-eye control at game pace.',
    ],
    'cla_perspective': [
        'Athlete-regulated constraints — the double-point gate rule, and any variation in gate-guarding, can be set by athletes themselves mid-game; this creates a richer tactical decision environment and reveals individual and team-level problem-solving strategies.',
        'Constrain to potentiate — the no-repeat-gate rule eliminates the most predictable attacking option after every score, continuously forcing new movement solutions without coach intervention.',
        'Perception-action coupling — both attacker and defender read the ball, their teammates, and opposition positions simultaneously; the multiple gate options mean no single action has a fixed cue.',
        'Self-organisation — with four scoring options and variable double-point gates, team attacking and defensive patterns emerge through play rather than being prescribed; observe what solutions emerge without intervening.',
    ],
    'coach_considerations': [
        'Start with gate-guarding OFF — the open game creates higher movement volume and more gate attempts. Introduce guarding only once athletes have the base movement patterns.',
        'Double-point gates are best introduced by athletes once they understand the basic game — ask them to agree which gate is double before the round starts. Watch how it changes their decision-making.',
        'The pass-through option (catch by a teammate) is harder to defend and should be encouraged once dribble-only is established.',
        'Teams of 3 create more complex passing and space-reading than 2v2 — use 3v3 when the group is ready for higher decision-making demand.',
        'Ball type changes the nature of the game significantly: a large round ball favours passing, a rugby ball introduces bounce uncertainty, a smaller ball rewards precision.',
    ],
    'levels': {
        'L1': '2v2 · Pass or dribble · No gate guarding · Open gates · 2 minutes',
        'L2': '2v2 · Pass or dribble · No gate guarding · One double-point gate · 2 minutes',
        'L3': '3v3 · Pass or dribble · No gate guarding · One double-point gate · 2 minutes',
        'L4': '3v3 · Pass or dribble · Gate guarding allowed · One double-point gate · 2 minutes',
        'L5': '3v3 · Pass or dribble · Gate guarding allowed · Two double-point gates · Athlete-set rules',
    },
    'alignment_label': 'MEASUREMENT TESTS THAT ALIGN',
    'measurement_tests': ['Diamond Gates', 'Diamond Dribble'],
    'tags': {
        'D1': ['Dynamic Locomotor'],
        'D2': ['Change of Direction Speed', 'Reactive Agility', 'Acceleration', 'Ball Control', 'Hand-Eye Coordination'],
        'D3': ['Athlete-Regulated Constraints', 'Constrain to Potentiate', 'Perception-Action Coupling', 'Self-Organisation', 'Representative Task Design'],
        'D4': ['Bilateral'],
        'D5': ['Task', 'Environmental', 'Interpersonal'],
        'D6': ['Large Ball', 'Gate / Cone'],
        'D7': ['Medium 5–15m'],
        'D8': ['Small Group 3–5', 'Team 6+'],
        'D9': ['Level 1', 'Level 2', 'Level 3'],
        'D10': ['Diamond Gates', 'Diamond Dribble'],
    },
},

{
    'slug': 'diamond-gates-team-dribbling',
    'title': 'Diamond Gates Team Dribbling',
    'badge': 'PROGRAMME GAME',
    'sport': '',
    'equipment': 'Large Ball / Gate / Cone',
    'measurement': '2–4 players per team  |  One team per diamond  |  Score = gates reached',
    'task': [
        'One team per diamond, 2–4 players. All players start in the centre square with a ball each.',
        'On signal, all players move simultaneously — each player dribbles from the centre square to any gate and returns.',
        'A gate scores 1 point each time an athlete dribbles to it and returns. All player scores combine for the team.',
        'Key rule — the same gate cannot be visited twice in a row by the same player.',
        'Play for a set time (e.g. 1 minute). Team vs Team across all diamonds.',
    ],
    'environment': (
        'Diamond: 4 gates + centre square. All players start in centre with a ball each. '
        'Dribble out (navy) · Return to centre (orange). 1 point per gate-and-return.'
    ),
    'sc_perspective': [
        'Change of direction speed (CODs) — the gate-to-centre-to-gate pattern with a ball creates repeated deceleration and re-acceleration demands identical to Diamond Gates, with ball control adding a concurrent physical challenge to every direction change.',
        'Ball manipulation/dribbling — maintaining ball control at pace with head up across the diamond under the combined pressure of gate selection, teammate movement and time constraint.',
        'Reactive agility — available gates shift continuously as other athletes move around the diamond; athletes must read the live situation and decide in real time while dribbling at speed.',
    ],
    'cla_perspective': [
        'Constrain to potentiate — the no-repeat-gate rule generates the same continuous direction-change demand as Diamond Gates, with the ball adding a second simultaneous constraint that athletes must solve without coaching.',
        'Attunement & calibration — each athlete calibrates their dribbling pace, deceleration point and gate approach to the diamond distances across the session; this emerges through play, not instruction.',
        'Functional locomotion — dribble, deceleration and direction-change patterns emerge entirely from the spatial constraint of the diamond; no movement technique is prescribed.',
    ],
    'coach_considerations': [
        'Enforce the no-repeat gate rule from the start — this is what drives continuous movement and decision-making.',
        'Encourage athletes to dribble with their head up to read the next gate before arriving; head-down dribbling collapses the reactive element of the game.',
        'Rotate ball types between rounds to develop dribbling solutions across sport contexts.',
        'Adjust diamond size to scale the challenge — a smaller diamond sharpens direction-change demands, a larger one extends the dribbling sprint.',
    ],
    'tags': {
        'D1': ['Dynamic Locomotor', 'Perceptual-Motor Speed'],
        'D2': ['Ball Manipulation / Dribbling', 'Change of Direction Speed', 'Reactive Agility'],
        'D3': ['Attunement & Calibration', 'Self-Organisation', 'Constrain to Potentiate'],
        'D4': ['Alternating'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Large Ball', 'Gate / Cone'],
        'D7': ['Large 15m+'],
        'D8': ['Small Group 3–5'],
        'D9': ['Level 1', 'Level 2'],
        'D10': ['Diamond Dribble', 'Diamond Gates', 'Cross-Family'],
    },
},

{
    'slug': 'ball-frog',
    'title': 'Ball Frog',
    'badge': 'PROGRAMME GAME',
    'sport': '',
    'equipment': 'Large Ball / Small Ball',
    'measurement': 'Pairs  |  Throw, Leap & Catch  |  Race or Distance',
    'task': [
        'Mark a start line and end line at 10m, 20m, or 25m. Teams of two line up at the start.',
        'First athlete throws the ball forward (self-feed), then immediately takes a standing jump as far as possible.',
        'Athlete must catch the ball in the air or upon landing. If caught, they mark their landing spot.',
        'Missed catch — no distance gained. Retrieve and throw again from the same spot.',
        'On a successful catch, the partner takes over from the landing spot. Roles alternate.',
        'Race format: first pair to end line wins. Distance format: furthest combined distance after a set number of leaps.',
    ],
    'environment': (
        'START → 10m → 20m → 25m TARGET. Two athletes leap alternately. '
        'A1 throws forward, leaps, catches in air or on landing, marks spot. '
        'A2 starts from landing spot and repeats. Roles alternate continuously.'
    ),
    'sc_perspective': [
        'Horizontal plyometric power — generating maximum distance from a standing leap, with the self-feed throw adding a concurrent coordination demand that makes the jump functionally different from a standard standing broad jump.',
        'Landing mechanics and force absorption — catching and absorbing the landing from a maximum-effort jump requires simultaneous deceleration through the lower limb and hand-eye coordination to complete the catch; the two demands compete for attentional resource at the moment of peak physical load.',
        'Hand-eye coordination under exertion — catching a self-thrown ball while airborne and at maximum physical output is a significantly higher coordination demand than catching at rest; it develops the coupling between explosive effort and fine motor control.',
    ],
    'cla_perspective': [
        'Perception-action coupling — the throw arc and jump trajectory are coupled as one continuous action; the athlete must read their own throw in flight while already committed to the leap. There is no opportunity to correct independently — throw and jump must be regulated together.',
        'Self-organisation — pairs discover the optimal throw-distance and height trade-off through play; a throw that is too far ahead costs a missed catch and no distance gained, too short wastes ground. The game provides immediate, unambiguous feedback without coach input.',
        'Constraining to attune — the self-feed rule means athletes cannot separate the throw from the jump or delegate the throw to a partner; this constraint forces each athlete to attune their own throw calibration to their jumping capacity, which varies by individual.',
    ],
    'coach_considerations': [
        'The throw distance is the key decision — the game self-corrects immediately (missed catch = no ground gained), so resist explaining the optimal throw distance. Let pairs find it themselves.',
        'Run multiple pairs simultaneously side by side in race format — the competitive pressure lifts jump intensity significantly compared to solo distance attempts.',
        'Ball size is a useful lever: a larger ball is easier to catch while airborne; a smaller ball sharpens the coordination demand and is a natural progression once pairs are finding their throw-distance calibration consistently.',
    ],
    'tags': {
        'D1': ['Explosive & Landing'],
        'D2': ['Plyometric Power', 'Landing Mechanics', 'Hand-Eye Coordination'],
        'D3': ['Perception-Action Coupling', 'Self-Organisation', 'Constrain to Afford', 'Functional Variability'],
        'D4': ['Bilateral'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Large Ball', 'Small Ball'],
        'D7': ['Large 15m+'],
        'D8': ['Pair'],
        'D9': ['Level 2', 'Level 3'],
        'D10': ['Grid Leap', 'Cross-Family'],
    },
},

{
    'slug': 'compass-ball',
    'title': 'Compass Ball',
    'badge': 'PROGRAMME GAME',
    'sport': '',
    'equipment': 'Large Ball / Gate / Cone',
    'measurement': '4 teams  |  2 simultaneous games  |  No ball movement while held',
    'task': [
        'Four teams. One court. Two games run simultaneously — one pair plays north-to-south, the other east-to-west, sharing the same space.',
        'Each pair of teams advances the ball into the opposing team\'s End Zone by passing, throwing, or kicking.',
        'Ball carrier cannot move — once you receive the ball you must stop and pass immediately.',
        'If the ball hits the ground or is mis-controlled, it\'s a turnover. Out of bounds — opposition throws/kicks in from the sideline.',
        'Key rule — point scored by catching the ball cleanly in the opposing team\'s End Zone. Restart from the goal line.',
        'Extension — open scoring: teams may score in any of the three End Zones they are not defending. The attacking team chooses their target end zone in real time, forcing defenders to cover all three directions simultaneously.',
    ],
    'environment': (
        'Single court. Teams A/B play N↔S. Teams C/D play E↔W. End Zones at each end of both orientations. '
        'Two simultaneous games share the same space at all times. '
        'Extension: each team defends 1 end zone and can attack any of the other 3.'
    ),
    'sc_perspective': [
        'Change of direction speed (CODs) — the shared court creates constant interruptions to direct movement paths; players must decelerate and re-route around athletes from the crossing game in real time.',
        'Reactive agility — tracking two simultaneous games means that the predictability of any passing lane or space is continuously disrupted by independent movement from the crossing game.',
        'Horizontal power — sharp first-step acceleration into space is essential on a court that closes rapidly as both games run in the same area simultaneously.',
    ],
    'cla_perspective': [
        'Landscape of affordances — two simultaneous games create a uniquely dense and dynamic affordance landscape; passing lanes, space and movement options change more rapidly than any single-game environment can produce.',
        'Constraining to attune — sharing the court with a crossing game forces athletes to attune their movement and passing decisions to a far denser, less predictable information field than standard game play.',
        'Self-organisation — teams discover passing combinations and movement solutions in the complex shared space without positional instruction; the environment shapes the solution entirely.',
    ],
    'coach_considerations': [
        'The shared court is intentional — athletes must track two games at once, dramatically increasing spatial and perceptual load without any change to the rules.',
        'The open-scoring extension is a significant step up: teams must now attack in any direction and defend against attacks from all three other end zones simultaneously. Introduce it once the base game is flowing.',
        'Encourage athletes to use kick passing as well as throwing to create different angles and space.',
        'Vary ball types across the two games to add differentiated challenge. Rotate team pairings and direction each round.',
    ],
    'tags': {
        'D1': ['Dynamic Locomotor', 'Perceptual-Motor Speed'],
        'D2': ['Reactive Agility', 'Change of Direction Speed', 'Hand-Eye Coordination', 'Foot-Eye Coordination'],
        'D3': ['Landscape of Affordances', 'Constraining to Attune', 'Self-Organisation', 'Perception-Action Coupling'],
        'D4': ['Alternating'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Large Ball', 'Gate / Cone'],
        'D7': ['Large 15m+'],
        'D8': ['Large Group 6+'],
        'D9': ['Level 2', 'Level 3'],
        'D10': ['Diamond Gates', 'Cross-Family'],
    },
},

{
    'slug': 'zone-ranger',
    'title': 'Zone Ranger',
    'badge': 'PROGRAMME GAME',
    'sport': '',
    'equipment': 'Large Ball / Gate / Cone',
    'measurement': '3v3  ·  Goals at Both Ends  |  3 Zones  ·  Fixed Roles  |  No Defenders in Goal Zone',
    'task': [
        'Set up a field with goals at both ends, divided into three zones: goal zones at each end and a middle zone.',
        'Each team of 3: Goalkeeper (GK) stays in own goal zone; Playmaker (PM) operates in middle zone; Attacker (ATT) stays in opponent\'s goal zone.',
        'No outfield defenders allowed inside either goal zone — only the GK defends there, creating a 1v1.',
        'Playmakers defend in middle zone to prevent the ball entering their own goal zone, and feed their attacker.',
        'Attacker must keep moving — no standing still for more than 3 seconds. A shot must be taken within 2 touches.',
        'Play to a set number of goals then rotate positions.',
    ],
    'environment': (
        'Three-zone field: TEAM A GOAL ZONE — MIDDLE ZONE — TEAM B GOAL ZONE. '
        'GK in own zone · PM in middle · ATT in opponent zone. No outfield defenders in goal zones.'
    ),
    'sc_perspective': [
        'Reactive agility — the 1v1 in the goal zone demands explosive first-step acceleration and body-positioning adjustments in response to the attacker\'s movement; no teammate can help, so all decisions are individual.',
        'Change of direction speed (CODs) — the playmaker must cover the full middle zone for both defensive recovery and forward feeding, generating frequent deceleration-and-redirect demands on a large lateral area.',
        'Spatial processing and field vision — all three roles require simultaneous tracking of ball position, teammate location, and opposition across multiple zones; the fixed structure isolates and develops this skill in each role independently.',
    ],
    'cla_perspective': [
        'Constraining to attune — the zone rules separate the perceptual-motor problem for each role; the attacker attunes to the goalkeeper\'s position, the playmaker to passing lanes and defensive pressure, the goalkeeper to the attacker\'s movement. Each constraint creates a distinct and focused information environment.',
        'Representative task design — the three fixed roles replicate real match-decision environments (finishing, distribution, goalkeeping) under genuine competitive pressure, making the game directly transferable to sport contexts.',
        'Perception-action coupling — the attacker reads the goalkeeper\'s positioning and weight distribution continuously to identify the optimal receiving pocket; the 2-touch limit prevents over-thinking and keeps coupling live.',
    ],
    'coach_considerations': [
        'The zone structure does the coaching — athletes discover their spatial responsibilities through the rules without instruction.',
        'The 3-second movement rule keeps the attacking zone active and prevents the attacker simply waiting at a fixed point.',
        'Rotating all three positions is essential — every athlete experiences the perceptual demands of all three roles across the session.',
        'To increase difficulty, reduce the 2-touch rule to 1 touch in the goal zone; to ease it, allow 3 touches and remove the 3-second rule initially.',
    ],
    'tags': {
        'D1': ['Dynamic Locomotor', 'Perceptual-Motor Speed'],
        'D2': ['Reactive Agility', 'Change of Direction Speed', 'Foot-Eye Coordination'],
        'D3': ['Constrain to Afford', 'Representative Task Design', 'Perception-Action Coupling', 'Self-Organisation'],
        'D4': ['Bilateral'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Large Ball', 'Gate / Cone'],
        'D7': ['Large 15m+'],
        'D8': ['Small Group 3–5', 'Large Group 6+'],
        'D9': ['Level 2', 'Level 3'],
        'D10': ['Diamond Gates', 'Cross-Family'],
    },
},

{
    'slug': 'out-of-the-kitchen',
    'title': 'Out of the Kitchen',
    'badge': 'PROGRAMME GAME',
    'sport': '',
    'equipment': 'Large Ball / Wall',
    'measurement': '3v3 (or 2v2)  |  Volleyball  |  First to 11 Points',
    'task': [
        'Set up a court ~6m wide × 10m long with a pickleball-height net. Mark a kitchen zone ~2m either side of the net.',
        'Standard volleyball contacts — all body parts. No player may contact the ball twice in a row. Up to 3 contacts per team.',
        'Kitchen rule: a player inside the kitchen zone may only defend (dig/receive/redirect). Cannot win a point from inside the kitchen.',
        'To score a point, the winning contact must be made from behind the kitchen line.',
        'Serve from behind baseline into the opposition half, beyond the kitchen line.',
        'Rally scoring. First to 11 points wins — win by 2.',
    ],
    'environment': (
        '~6m wide × 10m long court. Net at pickleball height (86–91cm). '
        'Kitchen zone ~2m either side of the net. Attack only from behind kitchen line.'
    ),
    'sc_perspective': [
        'Dynamic postural control — continuous court movement relative to the kitchen boundary requires athletes to maintain balance and body awareness across the full court while tracking ball flight; the unstable platform of constant reposition makes every contact a balance challenge.',
        'Reactive agility — reading the opponent\'s contact point, ball trajectory and kitchen position simultaneously to decide whether to hold, retreat, or commit to an attack from behind the line; the kitchen boundary compresses the available reaction time on each transition.',
        'Foot-eye and multi-surface coordination — volleyball contacts (dig, set, attack) from dynamic, often off-balance positions demand body-surface selection under time pressure; no single technique is reliable across all rally situations.',
    ],
    'cla_perspective': [
        'Constraining to attune — the kitchen rule creates a spatial information environment that athletes must attune to continuously; where you are on the court determines what you are allowed to do, coupling movement decisions to the scoring constraint at all times.',
        'Perception-action coupling — each player reads the opponent\'s position relative to the kitchen line before the ball arrives; an opponent deep in the kitchen signals a defensive contact, one behind the line signals an attack. This read shapes the receiver\'s preparation before the ball is struck.',
        'Self-organisation — teams discover their own attacking patterns, kitchen transitions, and court coverage through competitive play without positional instruction; the constraint shapes behaviour more efficiently than coaching.',
    ],
    'coach_considerations': [
        'The kitchen constraint is doing the coaching — athletes must solve court positioning relative to the scoring rule themselves. Avoid explaining tactics; let them figure out the transition problem.',
        'The lower net height is intentional — it increases rally length and keeps the game flowing, which is what generates the balance and reaction volume.',
        'Watch for athletes camped behind the kitchen line — this is the early defensive solution. As confidence grows, they will discover the court management needed to attack from behind the line consistently.',
        'Ball type is a useful lever: a volleyball slows play and rewards chest/set contacts; a football sharpens the reactive dig demand; a beach ball dramatically extends rallies for lower-ability groups.',
    ],
    'tags': {
        'D1': ['Balance & Postural Control', 'Perceptual-Motor Speed'],
        'D2': ['Dynamic Balance', 'Bilateral Balance', 'Foot-Eye Coordination', 'Reactive Agility'],
        'D3': ['Constraining to Attune', 'Perception-Action Coupling', 'Self-Organisation', 'Representative Task Design'],
        'D4': ['Bilateral'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Large Ball', 'Net / Wall'],
        'D7': ['Medium 5–15m'],
        'D8': ['Small Group 3–5'],
        'D9': ['Level 1', 'Level 2', 'Level 3'],
        'D10': ['Balance Catching'],
    },
},

{
    'slug': 'head-tennis',
    'title': 'Head Tennis',
    'badge': 'PROGRAMME GAME',
    'sport': '',
    'equipment': 'Large Ball / Wall / Net',
    'measurement': '2v2 (or 3v3)  |  Athlete-chosen rules  |  First to 11 Points',
    'task': [
        'Set up a court ~6m wide × 10m long with a pickleball-height net (86–91cm).',
        'Teams of 2v2. Players may use feet, knees, chest, and head. Hands and arms strictly out.',
        'Serve: drop the ball and kick from the hands or off a half-volley over the net.',
        'Key rule — before each game, teams agree their own ruleset by choosing one option from each of the three variables: (1) Touches per player, (2) Team contacts per side, (3) Bounces allowed.',
        'Key rule — rally scoring. First to 11 wins — win by 2. Teams may renegotiate rules between games.',
        'Rule variables — Touches per player: 1 / 2 / unlimited. Team contacts per side: 1 / 2 / 3. Bounces allowed: 0 / 1 / 2.',
    ],
    'environment': (
        '~6m wide × ~10m long court. Net at pickleball height (86–91cm). '
        'Teams agree their rule combination before each game. '
        'Harder: fewer touches, fewer contacts, fewer bounces. Easier: more of each.'
    ),
    'sc_perspective': [
        'Foot-eye coordination — multi-surface ball control (feet, knees, chest, head) requires continuous adaptable body-surface selection; no single technique is ever sufficient.',
        'Bilateral balance — receiving and redirecting the ball with non-dominant body surfaces under rally pressure demands dynamic postural control with no hand-stabilisation available.',
        'Reactive agility — tracking ball flight, spin and bounce angle to select and position the right body surface before the ball arrives; tighter touch and bounce rules compress decision time.',
    ],
    'cla_perspective': [
        'Constrain to afford — removing hands forces athletes to discover novel body-surface contact solutions not accessible in standard sport contexts; the constraint creates the learning environment.',
        'Athlete-regulated constraints — teams choosing their own touch, contact and bounce rules is a form of self-organised difficulty calibration; athletes implicitly reveal their current skill level through the ruleset they choose.',
        'Perception-action coupling — athlete reads ball flight, spin and angle to select the right body surface and position; the absence of a dominant limb makes this coupling more explicit and demanding than in hand-based sports.',
    ],
    'coach_considerations': [
        'Let teams choose their own rules without guidance — the ruleset they select tells you more about their current level than any assessment.',
        'Tighter rules (1 touch, 1 contact, no bounce) produce fast, reactive play and expose body-surface gaps. Looser rules (unlimited touch, 3 contacts, 2 bounces) build confidence and rally length.',
        'Ball type is a fourth difficulty dial: football = composed control; volleyball = slows play and rewards chest/head; tennis ball = sharpens reflexes and foot accuracy.',
        'Encourage teams to gradually tighten rules across games within a session as confidence builds — this creates natural progression without coach-directed instruction.',
    ],
    'tags': {
        'D1': ['Balance & Postural Control', 'Perceptual-Motor Speed'],
        'D2': ['Foot-Eye Coordination', 'Bilateral Balance', 'Reactive Agility', 'Proprioception'],
        'D3': ['Constrain to Afford', 'Self-Organisation', 'Perception-Action Coupling', 'Functional Variability'],
        'D4': ['Bilateral'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Large Ball', 'Wall'],
        'D7': ['Medium 5–15m'],
        'D8': ['Pair', 'Small Group 3–5'],
        'D9': ['Level 1', 'Level 2', 'Level 3'],
        'D10': ['Balance Catching', 'Cross-Family'],
    },
},

{
    'slug': 'find-the-gap',
    'title': 'Find the Gap',
    'badge': 'PROGRAMME GAME',
    'sport': '',
    'equipment': 'Large Ball / Gate / Cone',
    'measurement': '4 vs 4  |  25m × 20m pitch  |  2 goals each end',
    'task': [
        'Set up a pitch 25m wide by 20m long — deliberately wider than long. Place two small goals at each end, positioned wide (not in the centre).',
        '4v4 — no goalkeeper. Normal football rules apply.',
        'Teams attack the two goals at the opposite end and defend the two goals at their own end.',
        'A goal can be scored in either of the two wide goals — the defending team must cover both, creating natural gaps.',
        'Key rule — no coach instruction during play. Let the environment do the teaching.',
    ],
    'environment': (
        '25m wide × 20m long pitch. Two wide goals at each end (no centre goals). No goalkeeper. '
        'Wide pitch + two goals naturally invites width, switching, and gap-seeking.'
    ),
    'sc_perspective': [
        'Reactive agility — reading defensive shape and identifying which wide goal is exposed before the defence can recover; decisions must be made and acted on under time pressure.',
        'Change of direction speed (CODs) — switching play from one goal to the other demands rapid lateral repositioning for both attackers and defenders; the wider-than-long pitch amplifies the COD demand on both sides.',
        'Spatial processing and field vision — tracking two wide scoring options and the full opposition defensive shape simultaneously develops attentional breadth that transfers directly to multi-player sport environments.',
    ],
    'cla_perspective': [
        'Constraining to attune — the wide pitch and two-goal design creates the information environment for width, switching and gap-seeking to emerge; athletes attune to the available space without being told to use it.',
        'Landscape of affordances — two wide goals presented simultaneously create a richer action landscape than a single central goal; the environment invites players to perceive and act on multiple scoring options at once.',
        'Self-organisation — attacking shape, defensive cover and switching patterns all emerge through play without instruction; the design does the teaching.',
    ],
    'coach_considerations': [
        'Do not instruct during play — the pitch design is the constraint. Let the environment invite the behaviour.',
        'If teams score too easily, bring the two goals closer together to narrow the attacking window and increase the defensive cover challenge.',
        'If teams fail to use width, widen the pitch further — this makes it physically impossible to defend both goals from a central position.',
        'Ball type changes the game: a football rewards combination play; a rugby ball introduces a bounce variable that further disrupts defensive positioning.',
    ],
    'tags': {
        'D1': ['Dynamic Locomotor', 'Perceptual-Motor Speed'],
        'D2': ['Reactive Agility', 'Change of Direction Speed', 'Foot-Eye Coordination'],
        'D3': ['Constrain to Afford', 'Self-Organisation', 'Landscape of Affordances', 'Perception-Action Coupling'],
        'D4': ['Bilateral'],
        'D5': ['Environmental', 'Task'],
        'D6': ['Large Ball', 'Gate / Cone'],
        'D7': ['Large 15m+'],
        'D8': ['Small Group 3–5', 'Large Group 6+'],
        'D9': ['Level 2', 'Level 3'],
        'D10': ['Diamond Gates', 'Cross-Family'],
    },
},

{
    'slug': 'inside-running',
    'title': 'Inside Running',
    'badge': 'PROGRAMME GAME',
    'sport': '',
    'equipment': 'Large Ball / Gate / Cone',
    'measurement': 'Pairs  |  Hands or Feet  |  Self-Regulating Distance  |  First to 10 Points',
    'task': [
        'Set up a corridor 3m wide and 20m long. Mark a gate at 10m and a target line at 20m.',
        'Defender stands at the start line with the ball. Attacker stands 5m ahead in the corridor.',
        'To start each play, the defender passes the ball to the attacker. On the catch, the attacker immediately dribbles toward the 20m target (hands or feet). Defender gives chase from their passing position.',
        'Attacker scores 1 point for passing through the 10m gate untagged; 2 points for reaching the 20m target untagged.',
        'Defender scores 1 point for a successful tag (two-hand touch on the ball carrier) before the 20m line.',
        'Key rule — self-regulating distance: if the attacker scores, the starting gap reduces by 1 step next play (harder for the attacker). If the defender tags, the gap increases by 1 step next play (easier for the attacker). The game auto-calibrates to the pairing.',
        'Swap roles after an agreed number of plays. First to 10 points wins the pair contest.',
        'Ladder option — after each pair contest, winners move up to face the next pair, losers move down. Points accumulate across all matchups.',
    ],
    'environment': (
        '3m wide × 20m long corridor. DEF at start line · ATT starts 5m ahead. '
        'DEF passes to ATT to begin each play, then gives chase. '
        'Gate at 10m · Target at 20m. '
        'Gap adjusts by 1 step after each play — shorter if ATT scores, longer if DEF tags. '
        'Ladder option: winners rotate up, losers rotate down.'
    ),
    'sc_perspective': [
        'Linear speed and acceleration — the attacker must convert the passed ball into forward momentum immediately; the head-start gap means the defender\'s chase acceleration is the key physical contest.',
        'Ball control under pursuit — receiving the pass cleanly and transitioning to full-speed dribbling in a single movement, while tracking a closing defender, demands coordinated ball manipulation at match intensity.',
        'Change of direction speed (CODs) — within the tight corridor, pace variation, body shielding, and weight shifts replace directional evasion as the primary physical tools; both attacker and defender must react to each other\'s adjustments.',
    ],
    'cla_perspective': [
        'Athlete-regulated constraints — the self-regulating distance means the challenge level is set entirely by the athletes\' own performance; the gap shrinks when the attacker succeeds, expands when they don\'t. No coach calibration is needed and the game continuously sits at the edge of each athlete\'s capability.',
        'Constraining to attune — the narrow corridor removes lateral evasion as an option, attuning the attacker to pace, body position and shielding solutions they would not discover on a wide surface.',
        'Perception-action coupling — the pass-to-sprint start couples the attacker\'s reading of the ball delivery with their acceleration decision; the defender\'s chase is triggered by the attacker\'s first movement, making both athletes\' actions continuously coupled to each other.',
    ],
    'coach_considerations': [
        'The pass-to-start is important — it removes the artificial gun-start and makes the initiation feel game-like; the attacker must handle the ball first before running.',
        'The self-regulating distance is the key feature — resist adjusting it manually. Let the system calibrate the matchup; the gap will find its natural level for each pairing within a few plays.',
        'Watch whether attackers use pace changes and body shielding (effective) or try to run wide (corridor removes this option). The constraint is working if you see problem-solving, not frustration.',
        'The ladder format works well with groups of 6 or more — pairs compete simultaneously, then winners rotate up and losers rotate down after each round.',
    ],
    'levels': {
        'L1': '5m starting gap · Large round ball · Hands carry only',
        'L2': '5m starting gap · Large round ball · Hands or feet',
        'L3': '5m starting gap · Rugby ball · Hands carry only',
        'L4': 'Self-regulating gap (start at 5m) · Any ball · Hands or feet · Ladder format',
        'L5': 'Self-regulating gap (start at 3m) · Any ball · Hands or feet · Ladder format',
    },
    'alignment_label': 'MEASUREMENT TESTS THAT ALIGN',
    'measurement_tests': ['Diamond Dribble', 'Diamond Gates'],
    'tags': {
        'D1': ['Dynamic Locomotor', 'Perceptual-Motor Speed'],
        'D2': ['Linear Speed', 'Acceleration', 'Ball Manipulation / Dribbling', 'Change of Direction Speed'],
        'D3': ['Athlete-Regulated Constraints', 'Constraining to Attune', 'Perception-Action Coupling', 'Self-Organisation'],
        'D4': ['Bilateral'],
        'D5': ['Task', 'Environmental', 'Interpersonal'],
        'D6': ['Large Ball', 'Gate / Cone'],
        'D7': ['Large 15m+'],
        'D8': ['Pair', 'Large Group 6+'],
        'D9': ['Level 1', 'Level 2', 'Level 3'],
        'D10': ['Diamond Dribble', 'Diamond Gates'],
    },
},

{
    'slug': 'street-gaelic-football',
    'title': 'Street Gaelic Football',
    'badge': 'DONOR SPORT',
    'sport': '',
    'equipment': 'Large Ball / Gate / Cone',
    'measurement': '4 v 4  |  ½ Basketball Court  |  No contact',
    'task': [
        'Two teams of 4. Set up H-shaped goals at each end using cones and a crossbar.',
        'Ball advanced by kick-pass, handpass, or soloing. Players may carry for up to 4 steps before soloing or passing.',
        'Solo = drop the ball onto your foot and kick it back into your hands. Resets the 4-step count.',
        'No contact — dispossession by blocking a pass or intercepting only.',
        'Scoring: kick or handpass over the crossbar = 1 point. Kick into the net (below crossbar) = 3 points.',
        'Restart after score — goalkeeper distributes from the goal line.',
    ],
    'environment': (
        '½ basketball court. H-shaped goals at each end (over the bar = 1pt, under = 3pts). '
        'Free kick zone near goal. SOLO = drop ball and kick back to hands.'
    ),
    'sc_perspective': [
        'Reactive agility — reading opposition movement, ball flight and the kicking/passing decision of the ball carrier simultaneously demands real-time perceptual processing at game pace; the no-contact rule means all dispossession comes through anticipation and intercept timing, not physical pressure.',
        'Change of direction speed (CODs) — continuous off-ball movement to create and defend passing angles on a compact court generates frequent, unpredictable COD demands for all players across the full duration of the game.',
        'Foot-eye and hand-eye coordination — the solo technique (drop, kick, recatch) requires precise foot-eye sequencing under time pressure; catching in traffic demands hand-eye coordination from dynamic, unbalanced positions as players contest the ball.',
    ],
    'cla_perspective': [
        'Representative task design — the simplified Gaelic rule set preserves the core perception-action demands of the full game: reading ball flight, timing the solo, supporting runs off the ball, and attacking the two-score-value goal structure.',
        'Constraining to attune — the no-contact rule removes physical pressure as a defensive tool, which forces defenders to attune to passing cues and ball flight rather than using body positioning alone; this sharpens perceptual reading skills for all players.',
        'Self-organisation — the dual scoring system (1 point over the bar, 3 points below) creates a constant tactical decision environment that teams navigate without instruction; attacking shape, shot selection and support runs emerge through play.',
    ],
    'coach_considerations': [
        'Introduce the solo technique before the game begins — one or two reps per player is enough. It is the skill that makes the game distinct and keeps possession moving.',
        'Enforce no-contact from the first play — it is the constraint that generates the most off-ball movement and reactive decision-making, and it breaks down quickly if not maintained.',
        'The dual scoring system (1 vs 3 points) is a built-in tactical problem: encourage athletes to notice when they are taking the wrong shot option rather than pointing it out yourself.',
        'Rotate the goalkeeper each round so every athlete experiences the perceptual demands of reading incoming kicks from the goal position.',
    ],
    'tags': {
        'D1': ['Dynamic Locomotor', 'Perceptual-Motor Speed'],
        'D2': ['Foot-Eye Coordination', 'Hand-Eye Coordination', 'Reactive Agility', 'Change of Direction Speed'],
        'D3': ['Representative Task Design', 'Constraining to Attune', 'Self-Organisation', 'Perception-Action Coupling'],
        'D4': ['Asymmetric'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Large Ball', 'Gate / Cone'],
        'D7': ['Large 15m+'],
        'D8': ['Large Group 6+'],
        'D9': ['Level 1', 'Level 2', 'Level 3'],
        'D10': ['Diamond Gates'],
    },
},

{
    'slug': 'street-handball',
    'title': 'Street Handball',
    'badge': 'DONOR SPORT',
    'sport': '',
    'equipment': 'Large Ball / Gate / Cone',
    'measurement': '4 v 4  |  ½ Basketball Court  |  3 sec hold · 3 step max',
    'task': [
        'Divide into two teams of 4. Set up small goals at each end of the half basketball court.',
        'Ball advanced by passing or dribbling — no running with the ball.',
        '3-second rule — player holding must pass, shoot or begin dribbling within 3 seconds.',
        '3-step rule — player may take up to 3 steps after receiving. A dribble resets the count.',
        'D-zone — only the designated goalkeeper/defender may stand inside the D-zone. Attackers must shoot from outside.',
        'Goal scored — conceding team restarts from own goal line.',
    ],
    'environment': (
        '½ basketball court (~14m × 15m). Small goals at each end. '
        'D-zone in front of each goal. 3-sec/3-step rules govern possession.'
    ),
    'sc_perspective': [
        'Reactive agility — reading the ball carrier\'s passing intent and body orientation to intercept or reposition before the pass is released; the 3-second rule compresses decision windows for both attacker and defender, elevating the reactive demand across all positions.',
        'Change of direction speed (CODs) — creating and defending passing angles on a compact half-court generates continuous lateral COD demands; players must accelerate into space and decelerate into position repeatedly across the game.',
        'Hand-eye coordination under pressure — throwing and catching at game pace in traffic, often from off-balance or moving positions, requires coordinated hand-eye control that is significantly more demanding than isolated drill practice.',
    ],
    'cla_perspective': [
        'Representative task design — the 3-second, 3-step and D-zone rules replicate the core perceptual and spatial structure of full handball; the compressed court preserves the density of decision-making that makes the sport challenging.',
        'Constraining to attune — the time and step limits remove the option to hold the ball and wait; players must attune to passing options and space in real time rather than processing sequentially, which develops faster perceptual-decision coupling.',
        'Self-organisation — passing combinations, shooting angles and defensive positioning all emerge through competitive play without positional instruction; the D-zone creates a natural attacking problem that teams solve differently every round.',
    ],
    'coach_considerations': [
        'Enforce the 3-second and 3-step rules consistently from the first play — they are the constraints that generate the reactive decision demand. Slack enforcement produces a completely different (and less effective) game.',
        'Encourage quick combination passing rather than individual dribbling — the game\'s perceptual value comes from reading teammates and opposition, not from individual ball manipulation.',
        'Rotate the D-zone goalkeeper each round — the perceptual demands of reading incoming throws from goal position are distinct and every player benefits from them.',
        'If the group finds scoring too difficult, widen the goal slightly or move the D-zone line back rather than removing rules.',
    ],
    'tags': {
        'D1': ['Dynamic Locomotor', 'Perceptual-Motor Speed'],
        'D2': ['Hand-Eye Coordination', 'Reactive Agility', 'Change of Direction Speed'],
        'D3': ['Representative Task Design', 'Constraining to Attune', 'Self-Organisation', 'Perception-Action Coupling'],
        'D4': ['Asymmetric'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Large Ball', 'Gate / Cone'],
        'D7': ['Medium 5–15m'],
        'D8': ['Large Group 6+'],
        'D9': ['Level 1', 'Level 2'],
        'D10': ['Ball Control', 'Cross-Family'],
    },
},

{
    'slug': 'the-perfect-set',
    'title': 'The Perfect Set',
    'badge': 'PROGRAMME GAME',
    'sport': '',
    'equipment': 'Large Ball / Gate / Cone / Wall',
    'measurement': 'Pairs  |  Dig or Set  |  Race or Fewest Attempts',
    'task': [
        'Mark out a 3×3 grid of 9 zones on each side of the net, numbered 1–9. One pair plays across the net.',
        'One player starts the rally with a feed throw over the net into any zone — the only throw in the rally.',
        'From the moment the ball is returned, both players must dig or set only. No more throwing.',
        'Each time a player digs or sets from a zone not yet claimed, that zone scores a point.',
        'Key rule — if the ball hits the ground, the rally ends. All zones already claimed are kept.',
        'Win by claiming all 9 zones on your side first, or most zones after an agreed number of rallies.',
    ],
    'environment': (
        '3×3 grid (zones 1–9) on each side of a net. Feeder throws to any zone on partner\'s side. '
        'Partner digs or sets back. Ball must not bounce twice.'
    ),
    'sc_perspective': [
        'Foot-eye coordination — volleyball dig and set technique applied across nine different spatial positions.',
        'Bilateral balance — moving between zones under rally pressure requires constant body weight transfer.',
        'Hand-eye coordination — timing of dig and set contact from dynamic movement positions.',
    ],
    'cla_perspective': [
        'Constrain to afford — zone grid creates spatial targets that develop position-adaptive technique; athletes must adapt their technique to where they are, not just how they hit.',
        'Perception-action coupling — incoming throw must be read and coupled to zone movement and contact selection simultaneously.',
        'Self-organisation — pair develops their own zone strategy and sequencing without instruction.',
    ],
    'coach_considerations': [
        'Allowing pairs to choose their own zone order creates genuine decision-making.',
        'The fewest-attempts format rewards consistent contact quality over speed.',
    ],
    'tags': {
        'D1': ['Balance & Postural Control'],
        'D2': ['Foot-Eye Coordination', 'Bilateral Balance', 'Hand-Eye Coordination'],
        'D3': ['Constrain to Afford', 'Perception-Action Coupling', 'Self-Organisation', 'Representative Task Design'],
        'D4': ['Bilateral'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Large Ball', 'Gate / Cone', 'Wall'],
        'D7': ['Medium 5–15m'],
        'D8': ['Pair'],
        'D9': ['Level 1', 'Level 2'],
        'D10': ['Balance Catching', 'Cross-Family'],
    },
},

{
    'slug': 'fast-4s',
    'title': 'Fast 4s',
    'badge': 'PROGRAMME GAME',
    'sport': '',
    'equipment': 'Any Ball / Cones',
    'measurement': '4 vs 4  |  10m × 30m+ pitch  |  30-second possession clock',
    'task': [
        'Set up a pitch 10m wide and at least 30m long with a scoring zone at each end. Use any ball.',
        'Teams of 4. Defenders tag the ball carrier with a two-hand touch — a tag does not cause a turnover.',
        'A 30-second possession clock governs each attack. Clock starts the moment the attacking team receives the ball.',
        'Key rule — the attacking team\'s goal is to reach the scoring zone before 30 seconds expires. Tags slow play but do not end possession.',
        'Key rule — when the clock expires, the ball turns over to the opposition at the point of last play.',
        'After a score, the opposition restarts from their own scoring zone. Run multiple games side by side with larger groups.',
    ],
    'environment': (
        '10m wide × 30m+ long pitch. Scoring zones at each end. '
        '30-second possession clock starts when attacking team receives the ball. '
        'Tags do not cause turnover — only the clock does. Any ball.'
    ),
    'sc_perspective': [
        'Change of direction speed (CODs) — the 10m pitch width compresses the playing space, forcing rapid lateral movement and gap-reading under constant time pressure.',
        'Linear speed — explosive attacking runs into space are the primary scoring mechanism; the clock rewards athletes who can accelerate into gaps decisively.',
        'Horizontal power — first-step explosiveness out of a tag situation or from receiving the ball drives the team\'s ability to advance before the clock expires.',
    ],
    'cla_perspective': [
        'Constrain to potentiate — the 30-second clock replaces the touch count as the primary constraint, converting decision-making from contact management to continuous time-and-space problem solving.',
        'Self-organisation — teams discover attacking patterns, spacing and timing solutions through the temporal and spatial constraints of the narrow pitch without positional instruction.',
        'Functional locomotion — sprint, direction-change and gap-finding patterns emerge entirely from the clock and pitch constraints; no movement solution is prescribed.',
    ],
    'coach_considerations': [
        'The clock is the game — athletes must manage time collectively, not just react to individual tags. This shifts the team\'s thinking from contact counting to spatial awareness.',
        'Any ball works: use whatever is available or rotate ball types between rounds to vary the handling demands.',
        'The narrow 10m pitch is the key spatial constraint — it forces close defensive organisation and quick attacking decisions without instruction.',
        'Progress by reducing pitch width or shortening the clock. Run multiple games side by side simultaneously with larger groups.',
    ],
    'tags': {
        'D1': ['Dynamic Locomotor', 'Perceptual-Motor Speed'],
        'D2': ['Change of Direction Speed', 'Linear Speed', 'Horizontal Power', 'Reactive Agility'],
        'D3': ['Constrain to Potentiate', 'Self-Organisation', 'Functional Locomotion', 'Perception-Action Coupling'],
        'D4': ['Bilateral'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Large Ball', 'Gate / Cone'],
        'D7': ['Large 15m+'],
        'D8': ['Large Group 6+'],
        'D9': ['Level 2', 'Level 3'],
        'D10': ['Diamond Gates', 'Cross-Family'],
    },
},

{
    'slug': 'three-squared-programme',
    'title': 'Three Squared',
    'badge': 'PROGRAMME GAME',
    'sport': '',
    'equipment': 'Large Ball / Gate / Cone',
    'measurement': '2–12 participants  |  3 squares · 12 gates  |  Timed or points',
    'task': [
        'Set up three squares in a line — 5m×5m, 10m×10m, 15m×15m. One gate on each side. Shared-side gates align.',
        'Players enter through any gate. Aim: move through all three squares and all 12 gates as efficiently as possible.',
        'Once through a gate, players can move freely inside that square before exiting through any other gate.',
        'Timed version — each player completes all 12 gates as fast as possible. Record finishing time.',
        'Points version — each gate passed = 1 point. Set a time limit. Score = total gates by all players.',
        'Layer challenge using movement progressions: running → dribbling → passing.',
    ],
    'environment': (
        '5m×5m · 10m×10m · 15m×15m squares in a line. 12 gates total. '
        'Shared side gates align between squares. Enter via any gate in any order.'
    ),
    'sc_perspective': [
        'Change of direction speed (CODs) — the three nested squares demand rapid deceleration and re-acceleration at every gate, with the 5m square creating the sharpest angular demands of the set.',
        'Reactive agility — gate sequence and route are athlete-chosen in real time under time pressure; no prescribed path means continuous read-and-decide across all three scales.',
        'Horizontal power — first-step explosiveness from a gate position drives throughput; the reward for sharper acceleration is more gates reached per unit time.',
    ],
    'cla_perspective': [
        'Constrain to afford — the three nested square sizes create qualitatively different movement environments within a single activity; the 5m square affords sharp pivots, the 15m square affords sustained sprinting, and athletes naturally discover the different movement solutions each demands.',
        'Attunement & calibration — athletes calibrate their running pace, deceleration point and direction-change mechanics to each square\'s spatial scale across the session without instruction.',
        'Functional locomotion — sprint, deceleration and direction-change patterns emerge entirely from the spatial constraint of the nested squares; no movement technique is prescribed.',
    ],
    'coach_considerations': [
        'Three square sizes create a natural challenge progression — 5m demands sharp direction changes, 15m demands sustained movement. Athletes will self-sort across them.',
        'In the points version, encourage athletes to plan their route rather than moving randomly — the spatial problem of which square to hit next is a core part of the challenge.',
        'With larger groups, stagger start times by 15 seconds to avoid congestion at shared-side gates.',
        'Use the timed version for individual benchmarking and the points version for team competition.',
    ],
    'tags': {
        'D1': ['Dynamic Locomotor'],
        'D2': ['Change of Direction Speed', 'Ball Manipulation / Dribbling', 'Reactive Agility'],
        'D3': ['Constrain to Afford', 'Attunement & Calibration', 'Self-Organisation', 'Functional Locomotion'],
        'D4': ['Bilateral'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Large Ball', 'Gate / Cone'],
        'D7': ['Large 15m+'],
        'D8': ['Adaptable'],
        'D9': ['Level 1', 'Level 2', 'Level 3'],
        'D10': ['Diamond Gates', 'Diamond Dribble', 'Cross-Family'],
    },
},

# ── SPLIT STEP ────────────────────────────────────────────────────────────────

{
    'slug': 'split-decision',
    'title': 'Split Decision',
    'badge': 'PROGRAMME GAME',
    'sport': '',
    'equipment': 'Reflex Ball / Cones / Low Barrier (progression)',
    'measurement': 'Pairs  |  Alternating attack & defence  |  Timed or first to 15',
    'task': [
        'Set up the Split Step layout — rear gates 5 metres from the wall, goal gate 1 metre in front (4 metres from wall), bounce zone marked between 1m and 3m from the wall.',
        'Attacker stands at the rear gates with the reflex ball. Defender takes position at or behind the goal gate.',
        'Attacker throws the reflex ball against the wall so it lands in the bounce zone. The ball must bounce in the zone to count as a valid throw.',
        'Key rule — ATTACKER scores 1 point if the ball passes through the goal gate without being intercepted.',
        'Key rule — DEFENDER scores 1 point for each successful interception before the ball crosses the goal gate line.',
        'Play to a time limit (e.g. 2 minutes per role) or first to 15 points. Swap roles, then rotate opponents within the group — winners vs winners, or accumulate points across all rounds.',
        'Progression — place a low barrier between the rear gates and goal gate. Both attacker and defender must step over it on every play, adding an explosive stepping demand to both roles.',
    ],
    'environment': (
        'WALL at top. REAR GATES at 5m. GOAL GATE at 4m. BOUNCE ZONE between 1m–3m from wall. '
        'ATT at rear gates · DEF at goal gate. '
        'Ball through gate = ATT point. Interception = DEF point. '
        'Progression: low barrier between gates for both players to step over.'
    ),
    'sc_perspective': [
        'Reactive agility — the 4-sided reflex ball creates an unpredictable return trajectory; the defender must read the ball off the wall and initiate movement before the direction is confirmed.',
        'Change of direction speed (CODs) — the defender covers a lateral interception window from a stationary ready position; explosiveness off the split step determines whether the gate is protected.',
        'Explosive stepping / landing mechanics (progression) — the low barrier requires both attacker and defender to step over on every play, adding a plyometric demand to the reactive agility base of the game.',
    ],
    'cla_perspective': [
        'Perception-action coupling — attacker reads the defender\'s position to select throw angle; defender reads ball contact with the wall to initiate movement; both are simultaneously coupled to each other\'s decisions in real time.',
        'Constraining to attune — the bounce zone and gate rules constrain both roles to a specific information environment; the reflex ball ensures the defender cannot over-rely on anticipation and must attune to live ball flight.',
        'Self-organisation — both attacker and defender discover their own optimal strategies (throw angle, step timing, split step position) through competitive play without coaching; the dual-score structure ensures both roles remain genuinely contested.',
    ],
    'coach_considerations': [
        'The dual-score system is key — both roles are competitive, so role-swapping feels meaningful rather than one-sided.',
        'The reflex ball is essential — a standard ball removes the reactive unpredictability that makes the defender\'s interception genuinely reactive.',
        'Encourage defenders to hold a split step (weight forward, slight knee bend, feet active) just as the ball hits the wall — this is the technical carry-forward from the test.',
        'The barrier progression integrates Explosive & Landing across both roles simultaneously — the attacker must clear it on every throw attempt, the defender on every intercept attempt.',
        'First-to-15 format creates natural competitive tension. Accumulating points across opponents works well in larger groups.',
    ],
    'levels': {
        'L1': 'Standard setup · 5m rear gates · Timed 2 minutes per role',
        'L2': 'Standard setup · 5m rear gates · First to 15 points',
        'L3': '6m rear gates · First to 15 points',
        'L4': '7m rear gates · First to 15 points',
        'L5': '7m rear gates + low barrier · First to 15 points',
    },
    'alignment_label': 'MEASUREMENT TESTS THAT ALIGN',
    'measurement_tests': ['Split Step — Reflex Ball Interception'],
    'tags': {
        'D1': ['Perceptual-Motor Speed', 'Explosive & Landing'],
        'D2': ['Reactive Agility', 'Change of Direction Speed', 'Landing Mechanics', 'Deceleration'],
        'D3': ['Perception-Action Coupling', 'Constraining to Attune', 'Self-Organisation', 'Attunement & Calibration'],
        'D4': ['Bilateral'],
        'D6': ['Reflex Ball', 'Gate / Cone'],
        'D7': ['Minimal <5m×5m'],
        'D8': ['Pair', 'Small Group 3–5'],
        'D9': ['Level 1', 'Level 2', 'Level 3'],
        'D10': ['Split Step'],
    },
},

{
    'slug': 'split-step',
    'title': 'Split Step',
    'badge': 'TESTING GAME',
    'sport': '',
    'equipment': 'Reflex Ball / Cones',
    'measurement': '1 min per attempt  |  Individual athlete  |  Score = successful interceptions',
    'task': [
        'Set up rear gates 5 metres from the wall with a second goal gate 1 metre in front (4 metres from wall). '
        'Mark the bounce zone with two cones — one 1 metre from the wall, one 1 metre in front of the goal gate.',
        'Athlete takes position at or behind the goal gate.',
        'From the rear gates, the thrower throws the reflex ball against the wall — the ball must bounce in the bounce zone on its return.',
        'Key rule — the athlete moves to intercept the ball before it passes back through the goal gate.',
        'Key rule — each successful interception scores 1 point. The ball must be stopped before crossing the goal gate line.',
        'Ball must land in the bounce zone to count as a valid throw — if not, the throw is retaken.',
    ],
    'environment': (
        'WALL at top. REAR GATES at 5m. GOAL GATE at 4m (1m in front of rear gates). '
        'BOUNCE ZONE between 1m and 3m from wall (marked by 2 cones). '
        'Athlete defends goal gate. Ball thrown from rear gates must bounce in zone before athlete intercepts.'
    ),
    'sc_perspective': [
        'Reactive agility — the 4-sided reflex ball creates an unpredictable trajectory that demands instantaneous read-and-respond movement.',
        'Split step mechanics — ideal entry point for training the split step: athlete must be in a ready athletic position at ball contact with the wall to react effectively.',
        'Deceleration and change of direction — intercepting requires rapid braking and lateral or diagonal movement from the goal gate position.',
    ],
    'cla_perspective': [
        'Perception-action coupling — the wall bounce and reflex ball combine to make anticipation unreliable; the athlete must use real-time perceptual information to guide movement.',
        'Constraining to attune — the bounce zone rule constrains the throw and focuses the athlete\'s attention on reading the ball as it enters the return flight path.',
        'Self-organisation — no prescribed interception technique; athletes discover their own efficient movement solutions to cover the goal gate under time pressure.',
    ],
    'coach_considerations': [
        'The 4-sided reflex ball is essential — a standard ball removes the reactive unpredictability that makes this game effective.',
        'Encourage athletes to hold a split step (weight forward, slight knee bend, feet active) just as the ball hits the wall.',
        'Replicate the same setup across testing sessions for reliable scoring comparisons.',
    ],
    'levels': {
        'L1': 'Rear gates 5 metres from wall · 1 minute',
        'L2': 'All gates back 1 metre — rear gates at 6 metres · 1 minute',
        'L3': 'All gates back 2 metres — rear gates at 7 metres · 1 minute',
        'L4': '7 metre setup · 45 seconds',
        'L5': '7 metre setup · 30 seconds',
    },
    'measurement_tests': [
        'Split Step — Reflex Ball Interception',
    ],
    'alignment_label': 'MEASUREMENT TESTS THAT ALIGN',
    'tags': {
        'D1': ['Perceptual-Motor Speed'],
        'D2': ['Reactive Agility', 'Change of Direction Speed', 'Split Step Mechanics', 'Deceleration'],
        'D3': ['Perception-Action Coupling', 'Attunement & Calibration', 'Self-Organisation'],
        'D4': ['Bilateral'],
        'D5': ['Task', 'Environmental'],
        'D6': ['Reflex Ball', 'Gate / Cone', 'Wall'],
        'D7': ['Moderate 5m×5m–10m×10m'],
        'D8': ['Individual'],
        'D9': ['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5'],
        'D10': ['Split Step'],
    },
},

]  # end ALL_CARDS
