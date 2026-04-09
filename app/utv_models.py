"""
Curated UTV/ATV model variants for smart dropdown suggestions.
NHTSA only returns base model names; this covers specific trims/variants.
Falls back to NHTSA for makes not listed here.
"""

UTV_MODELS = {
    'Polaris': [
        # RZR Sport
        'RZR 200 EFI', 'RZR 570', 'RZR 570 Trail',
        'RZR 900', 'RZR 900S', 'RZR 900 Trail',
        'RZR XP 1000', 'RZR XP 4 1000',
        'RZR XP Turbo', 'RZR XP 4 Turbo',
        'RZR XP Turbo S', 'RZR XP 4 Turbo S',
        'RZR Pro XP', 'RZR Pro XP 4',
        'RZR Pro R', 'RZR Pro R 4', 'RZR Pro R Ultimate',
        'RZR Turbo R', 'RZR Turbo R 4',
        # Ranger Utility
        'Ranger 150 EV', 'Ranger 500',
        'Ranger 570', 'Ranger 570 SP', 'Ranger EV',
        'Ranger XP 900', 'Ranger Crew 570',
        'Ranger XP 1000', 'Ranger Crew XP 1000',
        'Ranger XP Kinetic',
        # General
        'General 1000', 'General 1000 EPS',
        'General 4 1000', 'General 4 1000 EPS',
        'General XP 1000', 'General XP 4 1000',
        # Sportsman ATV
        'Sportsman 110 EFI', 'Sportsman 450 HO',
        'Sportsman 570', 'Sportsman 570 Trail',
        'Sportsman 850', 'Sportsman XP 1000',
        # ACE
        'ACE 500', 'ACE 900', 'ACE 900 EPS', 'ACE 900 XC',
    ],
    'Can-Am': [
        # Maverick Trail/Sport
        'Maverick Trail 800', 'Maverick Trail 1000',
        'Maverick Trail DPS 800', 'Maverick Trail DPS 1000',
        'Maverick Sport 1000', 'Maverick Sport 1000R',
        # Maverick X3
        'Maverick X3', 'Maverick X3 Turbo', 'Maverick X3 Turbo R',
        'Maverick X3 Turbo RR', 'Maverick X3 Turbo RR 64',
        'Maverick X3 DS Turbo R', 'Maverick X3 RS Turbo R',
        'Maverick X3 X mr Turbo', 'Maverick X3 X mr Turbo RR',
        'Maverick X3 X rs Turbo R', 'Maverick X3 X rs Turbo RR',
        'Maverick X3 MAX Turbo R', 'Maverick X3 MAX Turbo RR',
        'Maverick X3 MAX X rs Turbo RR',
        # Defender Utility
        'Defender HD5', 'Defender HD7', 'Defender HD9', 'Defender HD10',
        'Defender HD10 Pro', 'Defender MAX HD5', 'Defender MAX HD10',
        'Defender MAX HD10 Pro', 'Defender 6x6 HD10',
        # Commander
        'Commander 700', 'Commander 800R', 'Commander 1000',
        'Commander DPS 1000', 'Commander XT 1000', 'Commander XT-P 1000',
        'Commander MAX XT 1000', 'Commander MAX XT-P 1000',
        # Outlander ATV
        'Outlander 450', 'Outlander 570', 'Outlander 650',
        'Outlander 850', 'Outlander 1000R',
        'Outlander MAX 450', 'Outlander MAX 570', 'Outlander MAX 850', 'Outlander MAX 1000R',
        # Renegade ATV
        'Renegade 570', 'Renegade 650', 'Renegade 850', 'Renegade 1000R',
        'Renegade X mr 850', 'Renegade X mr 1000R',
    ],
    'Yamaha': [
        # YXZ Sport
        'YXZ1000R', 'YXZ1000R SE', 'YXZ1000R SS', 'YXZ1000R SS SE',
        # Wolverine
        'Wolverine X2 850', 'Wolverine X2 R-Spec 850',
        'Wolverine X4 850', 'Wolverine X4 SE 850',
        'Wolverine RMAX2 1000', 'Wolverine RMAX2 1000 R-Spec',
        'Wolverine RMAX2 1000 XT-R',
        'Wolverine RMAX4 1000', 'Wolverine RMAX4 1000 XT-R',
        # Grizzly ATV
        'Grizzly 660', 'Grizzly 700', 'Grizzly 700 EPS', 'Grizzly 700 SE',
        # Kodiak ATV
        'Kodiak 450', 'Kodiak 700', 'Kodiak 700 SE',
        # Rhino (older)
        'Rhino 450', 'Rhino 660', 'Rhino 700',
        # Viking
        'Viking 700', 'Viking VI EPS', 'Viking VI EPS SE',
        # Raptor ATV
        'Raptor 700', 'Raptor 700R', 'Raptor 90',
        # Rancher/Bruin
        'Rancher 350', 'Rancher 400', 'Rancher 420', 'Rancher 450',
    ],
    'Honda': [
        # Talon Sport
        'Talon 1000R', 'Talon 1000X', 'Talon 1000R-4', 'Talon 1000X-4',
        'Talon 1000R FOX Live Valve',
        # Pioneer Utility
        'Pioneer 500', 'Pioneer 520',
        'Pioneer 700', 'Pioneer 700-4',
        'Pioneer 1000', 'Pioneer 1000-5',
        'Pioneer 1000-6 Crew',
        # Foreman ATV
        'FourTrax Foreman 4x4', 'FourTrax Foreman ES 4x4',
        'FourTrax Foreman Rubicon 4x4', 'FourTrax Foreman Rubicon DCT',
        # Rancher ATV
        'FourTrax Rancher 420 4x4', 'FourTrax Rancher 420 ES',
        'FourTrax Rancher 420 DCT IRS EPS',
        # Recon
        'FourTrax Recon 250',
        # TRX
        'TRX90X', 'TRX250X', 'TRX400X', 'TRX450R',
    ],
    'Kawasaki': [
        # Teryx SxS
        'Teryx 800', 'Teryx4 800', 'Teryx4 S 800',
        'Teryx KRX 1000', 'Teryx KRX 1000 Trail Edition',
        'Teryx KRX 1000 eS', 'Teryx KRX4 1000', 'Teryx KRX4 1000 Trail Edition',
        # Mule Utility
        'Mule 610 4x4', 'Mule SX 4x4', 'Mule SX 4x4 XC',
        'Mule PRO-FX EPS', 'Mule PRO-FXR', 'Mule PRO-FXT EPS',
        'Mule PRO-DX EPS', 'Mule PRO-DXT EPS', 'Mule PRO-MX EPS',
        # Brute Force ATV
        'Brute Force 300', 'Brute Force 750 4x4i', 'Brute Force 750 4x4i EPS',
        # KFX ATV
        'KFX 50', 'KFX 90', 'KFX 450R',
    ],
    'Arctic Cat': [
        'Wildcat Sport', 'Wildcat Sport LTD', 'Wildcat Trail',
        'Wildcat Trail LTD', 'Wildcat X', 'Wildcat XX',
        'Prowler 500', 'Prowler 650', 'Prowler 700',
        'Prowler Pro', 'Prowler Pro Crew',
        'Alterra 90', 'Alterra 150', 'Alterra 300',
        'Alterra 450', 'Alterra 570', 'Alterra 600', 'Alterra 700',
        'Alterra TRV 700', 'Alterra MudPro 700 LTD',
    ],
    'Textron': [
        'Wildcat XX', 'Wildcat Sport LTD',
        'Prowler Pro', 'Prowler Pro Crew',
        'Stampede 900', 'Stampede 4 900',
        'Alterra 300', 'Alterra 450', 'Alterra 570', 'Alterra 700',
    ],
    'CFMOTO': [
        'ZForce 500 Trail', 'ZForce 800 Trail', 'ZForce 800 EX',
        'ZForce 950 Sport', 'ZForce 950 Sport Trail',
        'ZForce 1000 Sport', 'ZForce 1000 Sport Trail',
        'UForce 500', 'UForce 600', 'UForce 800', 'UForce 1000',
        'CForce 300', 'CForce 400', 'CForce 500', 'CForce 600', 'CForce 800',
    ],
    'Kubota': [
        'RTV500', 'RTV900', 'RTV1100',
        'RTV-X900', 'RTV-X1100', 'RTV-X1120D', 'RTV-X1100C',
        'RTV-XG850 Sidekick',
    ],
    'John Deere': [
        'Gator XUV 560', 'Gator XUV 560 S4',
        'Gator XUV590i', 'Gator XUV590i S4',
        'Gator XUV825M', 'Gator XUV835M',
        'Gator XUV855M', 'Gator XUV865M',
        'Gator HPX615E', 'Gator HPX815E',
        'Gator TS 4x2', 'Gator TX 4x2', 'Gator TH 6x4',
    ],
    'Kioti': [
        'K9 2400', 'K9 2400 Crew',
    ],
    'Massimo': [
        'Buck 450', 'Buck 450X', 'MSU 500', 'MSU 700', 'MSU 800',
        'T-Boss 410', 'T-Boss 550', 'T-Boss 750',
        'Warrior 1000', 'Warrior 800',
    ],
    'Hisun': [
        'Strike 250', 'Strike 550', 'Strike 1000',
        'Sector 450', 'Sector 550', 'Sector 750', 'Sector 1000',
        'Tactic 750', 'Tactic 1000',
        'Mars 700', 'Mars 1000',
    ],
    'Kymco': [
        'UXV 450i', 'UXV 500i', 'UXV 700i', 'UXV 700i LE',
        'MXU 450i', 'MXU 500i', 'MXU 700i',
    ],
    'Suzuki': [
        'KingQuad 400', 'KingQuad 450', 'KingQuad 500', 'KingQuad 750',
        'LT-A400', 'LT-A450X', 'LT-A500XP', 'LT-A750XP',
        'LT-Z400', 'LT-Z50', 'LT-Z90',
    ],
}
