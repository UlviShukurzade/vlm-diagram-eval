"""Mermaid diagram fixtures.

Harvested from the ``__main__`` block of the original
``mermaid_parser_service/parser_service copy.py``, where they were collected
during development but never runnable as tests.
"""

STATE_DIAGRAM = """stateDiagram-v2
    [*] --> Idle
    
    state Idle {
        [*] --> Ready
        Ready --> Processing: Start
        Processing --> Ready: Complete
    }
    
    Idle --> Active: Activate
    
    state Active {
        [*] --> Running
        Running --> Paused: Pause
        Paused --> Running: Resume
        Running --> Error: Fail
        Error --> Running: Retry
    }
    
    Active --> Idle: Deactivate
    Active --> [*]: Shutdown
    
    note right of Active: System is fully operational
    note left of Idle: System is on standby
    """

MERMAID = """
    graph LR;
    registry(Patch Registry)
    dlopen[dlopen patch p1.so]
    dlsym(dlsym relevant parts)
    supported(Atomically live-patch)
    nosupport(Lock required live-patch)

    registry -->|Available Patches| dlopen
    dlopen -->|filter symbols| dlsym
    dlsym -->|Compiler w/ live patch support| supported
    dlsym -->|W/out live patch support| nosupport
    """

MINIMAL = """
    graph TD;
        A-->B-->C
        A-->C
    """

NESTED_LAYERS = """graph TD
    subgraph Forest Garden Layers
        C[Canopy Layer]
        S[Shrub Layer]
        H[Herbaceous Layer]
        R[Root Layer]
        M[Soil Microbiome]
    end
    subgraph System Architecture Layers
        UI[User Interface]
        ML[Middle Logic]
        DS[Data Services]
        DB[Database]
        IS[Infrastructure]
    end
    C --- UI
    S --- ML
    H --- DS
    R --- DB
    M --- IS
    C --> S
    S --> H
    H --> R
    R --> M
    UI --> ML
    ML --> DS
    DS --> DB
    DB --> IS"""

MERMAID_CLASS_DIAGRAM = """classDiagram
  direction LR
  ItemSystem ..> EnumRef:use
  Charactersystem ..> EnumRef:use
  Charactersystem ..> ItemSystem:use
  GameManager ..> ItemSystem:use
  Player ..> GameManager:use
  Player ..> Charactersystem:use
  Monster ..> Charactersystem:use
  Player --|> Monobehavior:extend
  Monster --|> Monobehavior:extend
  Charactersystem --|> Monobehavior:extend
  ItemSystem --|> ScriptableObject:extend
  ItemSystem --|> Monobehavior:extend
  class Monobehavior{
    <<Unity Class>>
    ...
    ...()
  }
  class ScriptableObject{
    <<Unity Class>>
    ...
    ...()
  }
  class EnumRef{
  }
  class ItemSystem{
  }
  class Charactersystem{
  }
  class GameManager{
  }
  class Player{
  }
  class Monster{
  }"""

MERMAID_YES_NO = """flowchart TD
    A["User Requests Protected Route"] --> B{"Is User Authenticated?"}
    B -->|"Yes"| C["Render Requested Component"]
    B -->|"No"| D["Redirect to Login Page"]"""

FLOWCHART_49441_65 = """flowchart LR
group[APT19] --> T1547.001[Registry Run Keys / Startup Folder]
group[APT19] --> T1059.001[PowerShell]
group[APT19] --> T1564.003[Hidden Window]
group[APT19] --> T1016[System Network Configuration Discovery]
group[APT19] --> T1033[System Owner/User Discovery]
group[APT19] --> T1218.011[Rundll32]
group[APT19] --> T1112[Modify Registry]
group[APT19] --> T1189[Drive-by Compromise]
group[APT19] --> T1543.003[Windows Service]
group[APT19] --> T1071.001[Web Protocols]
group[APT19] --> T1059[Command and Scripting Interpreter]
group[APT19] --> T1027.013[Encrypted/Encoded File]
group[APT19] --> T1566.001[Spearphishing Attachment]
group[APT19] --> T1204.002[Malicious File]
group[APT19] --> T1082[System Information Discovery]
group[APT19] --> T1132.001[Standard Encoding]
group[APT19] --> T1588.002[Tool]
group[APT19] --> T1574.002[DLL Side-Loading]
group[APT19] --> T1218.010[Regsvr32]
group[APT19] --> T1140[Deobfuscate/Decode Files or Information]
group[APT19] --> T1027.010[Command Obfuscation]
T1059.001[PowerShell] --> M1042[Disable or Remove Feature or Program]
T1059.001[PowerShell] --> M1049[Antivirus/Antimalware]
T1059.001[PowerShell] --> M1045[Code Signing]
T1059.001[PowerShell] --> M1026[Privileged Account Management]
T1059.001[PowerShell] --> M1038[Execution Prevention]
T1564.003[Hidden Window] --> M1038[Execution Prevention]
T1564.003[Hidden Window] --> M1033[Limit Software Installation]
T1218.011[Rundll32] --> M1050[Exploit Protection]
T1112[Modify Registry] --> M1024[Restrict Registry Permissions]
T1189[Drive-by Compromise] --> M1050[Exploit Protection]
T1189[Drive-by Compromise] --> M1051[Update Software]
T1189[Drive-by Compromise] --> M1048[Application Isolation and Sandboxing]
T1189[Drive-by Compromise] --> M1021[Restrict Web-Based Content]
T1543.003[Windows Service] --> M1040[Behavior Prevention on Endpoint]
T1543.003[Windows Service] --> M1028[Operating System Configuration]
T1543.003[Windows Service] --> M1047[Audit]
T1543.003[Windows Service] --> M1045[Code Signing]
T1543.003[Windows Service] --> M1018[User Account Management]
T1071.001[Web Protocols] --> M1031[Network Intrusion Prevention]
T1059[Command and Scripting Interpreter] --> M1045[Code Signing]
T1059[Command and Scripting Interpreter] --> M1042[Disable or Remove Feature or Program]
T1059[Command and Scripting Interpreter] --> M1038[Execution Prevention]
T1059[Command and Scripting Interpreter] --> M1049[Antivirus/Antimalware]
T1059[Command and Scripting Interpreter] --> M1026[Privileged Account Management]
T1059[Command and Scripting Interpreter] --> M1021[Restrict Web-Based Content]
T1059[Command and Scripting Interpreter] --> M1040[Behavior Prevention on Endpoint]
T1027.013[Encrypted/Encoded File] --> M1049[Antivirus/Antimalware]
T1027.013[Encrypted/Encoded File] --> M1040[Behavior Prevention on Endpoint]
T1566.001[Spearphishing Attachment] --> M1049[Antivirus/Antimalware]
T1566.001[Spearphishing Attachment] --> M1031[Network Intrusion Prevention]
T1566.001[Spearphishing Attachment] --> M1054[Software Configuration]
T1566.001[Spearphishing Attachment] --> M1017[User Training]
T1566.001[Spearphishing Attachment] --> M1021[Restrict Web-Based Content]
T1204.002[Malicious File] --> M1038[Execution Prevention]
T1204.002[Malicious File] --> M1040[Behavior Prevention on Endpoint]
T1204.002[Malicious File] --> M1017[User Training]
T1132.001[Standard Encoding] --> M1031[Network Intrusion Prevention]
T1588.002[Tool] --> M1056[Pre-compromise]
T1574.002[DLL Side-Loading] --> M1051[Update Software]
T1574.002[DLL Side-Loading] --> M1013[Application Developer Guidance]
T1218.010[Regsvr32] --> M1050[Exploit Protection]
T1027.010[Command Obfuscation] --> M1040[Behavior Prevention on Endpoint]
T1027.010[Command Obfuscation] --> M1049[Antivirus/Antimalware]"""

FLOWCHART_49441_65_GEN = """graph TD
    subgraph ATTACK TECHNIQUES
        APT19 --> RegistryRunKeysorStartupFolder[Registry Run Keys or Startup Folder]
        APT19 --> PowerShell[PowerShell]
        APT19 --> CommandandScriptingInterpreter[Command and Scripting Interpreter]
        APT19 --> SystemNetworkConfigurationDiscovery[System Network Configuration Discovery]
        APT19 --> SystemOwnerUserDiscovery[System Owner/User Discovery]
        APT19 --> HiddenWindow[Hidden Window]
        APT19 --> EncryptedEncodedFile[Encrypted/Encoded File]
        APT19 --> Rundll32[Rundll32]
        APT19 --> CommandObfuscation[Command Obfuscation]
        APT19 --> Regsvr32[Regsvr32]
        APT19 --> ModifyRegistry[Modify Registry]
        APT19 --> DrivebyCompromise[Drive-by Compromise]
        APT19 --> WindowsService[Windows Service]
        APT19 --> MaliciousFile[Malicious File]
        APT19 --> SystemInformationDiscovery[System Information Discovery]
        APT19 --> SpearphishingAttachment[Spearphishing Attachment]
        APT19 --> DLLSide-Loading[DLL Side-Loading]
        APT19 --> WebProtocols[Web Protocols]
        APT19 --> StandardEncoding[Standard Encoding]
        APT19 --> DeobfuscateDecodeFilesorInformation[Deobfuscate/Decode Files or Information]
        APT19 --> Tool[Tool]
    end

    subgraph DEFENSES
        DisableorRemoveFeatureorProgram[Disable or Remove Feature or Program]
        AntivirusAntimalware[Antivirus/Antimalware]
        CodeSigning[Code Signing]
        PrivilegedAccountManagement[Privileged Account Management]
        ExecutionPrevention[Execution Prevention]
        LimitSoftwareInstallation[Limit Software Installation]
        ExploitProtection[Exploit Protection]
        RestrictRegistryPermissions[Restrict Registry Permissions]
        UpdateSoftware[Update Software]
        ApplicationIsolationandSandboxing[Application Isolation and Sandboxing]
        RestrictWeb-BasedContent[Restrict Web-Based Content]
        BehaviorPreventiononEndpoints[Behavior Prevention on Endpoints]
        OperatingSystemConfiguration[Operating System Configuration]
        Audit[Audit]
        UserAccountManagement[User Account Management]
        NetworkIntrusionPrevention[Network Intrusion Prevention]
        SoftwareConfiguration[Software Configuration]
        UserTraining[User Training]
        Pre-compromise[Pre-compromise]
        ApplicationDeveloperGuidance[Application Developer Guidance]
    end

    RegistryRunKeysorStartupFolder --> DisableorRemoveFeatureorProgram
    PowerShell --> AntivirusAntimalware
    CommandandScriptingInterpreter --> AntivirusAntimalware
    CommandandScriptingInterpreter --> CodeSigning
    CommandandScriptingInterpreter --> PrivilegedAccountManagement
    CommandandScriptingInterpreter --> ExecutionPrevention
    SystemNetworkConfigurationDiscovery --> Audit
    SystemOwnerUserDiscovery --> Audit
    SystemOwnerUserDiscovery --> UserAccountManagement
    HiddenWindow --> AntivirusAntimalware
    HiddenWindow --> NetworkIntrusionPrevention
    EncryptedEncodedFile --> AntivirusAntimalware
    EncryptedEncodedFile --> CodeSigning
    EncryptedEncodedFile --> LimitSoftwareInstallation
    EncryptedEncodedFile --> ExploitProtection
    Rundll32 --> AntivirusAntimalware
    CommandObfuscation --> AntivirusAntimalware
    CommandObfuscation --> ExploitProtection
    CommandObfuscation --> RestrictRegistryPermissions
    Regsvr32 --> AntivirusAntimalware
    Regsvr32 --> ExploitProtection
    Regsvr32 --> RestrictRegistryPermissions
    ModifyRegistry --> AntivirusAntimalware
    ModifyRegistry --> RestrictRegistryPermissions
    DrivebyCompromise --> UpdateSoftware
    DrivebyCompromise --> ApplicationIsolationandSandboxing
    DrivebyCompromise --> RestrictWeb-BasedContent
    WindowsService --> AntivirusAntimalware
    MaliciousFile --> AntivirusAntimalware
    MaliciousFile --> BehaviorPreventiononEndpoints
    MaliciousFile --> LimitSoftwareInstallation
    SystemInformationDiscovery --> Audit
    SpearphishingAttachment --> AntivirusAntimalware
    SpearphishingAttachment --> BehaviorPreventiononEndpoints
    SpearphishingAttachment --> OperatingSystemConfiguration
    SpearphishingAttachment --> SoftwareConfiguration
    SpearphishingAttachment --> UserTraining
    DLLSide-Loading --> CodeSigning
    DLLSide-Loading --> ExecutionPrevention
    WebProtocols --> NetworkIntrusionPrevention
    StandardEncoding --> NetworkIntrusionPrevention
    DeobfuscateDecodeFilesorInformation --> NetworkIntrusionPrevention
    Tool --> Pre-compromise
    Tool --> ApplicationDeveloperGuidance"""

ALL_DIAGRAMS = {
    "state_diagram": STATE_DIAGRAM,
    "mermaid": MERMAID,
    "minimal": MINIMAL,
    "nested_layers": NESTED_LAYERS,
    "mermaid_class_diagram": MERMAID_CLASS_DIAGRAM,
    "mermaid_yes_no": MERMAID_YES_NO,
    "flowchart_49441_65": FLOWCHART_49441_65,
    "flowchart_49441_65_gen": FLOWCHART_49441_65_GEN,
}
