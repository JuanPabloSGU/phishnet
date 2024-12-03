# PhishNet

PhishNet is a Machine Learning tool designed to protect users from phishing attacks. By leveraging advanced models like HTMLGCNCNN and URLBERT, PhishNet provides real-time phishing detection through a user-friendly website and Chrome extension.

---

## Table of Contents
- [Project Overview](#project-overview)
- [Features](#features)
- [Installation](#installation)
  - [Website Access](#website-access)
  - [Chrome Extension](#chrome-extension)
- [Usage](#usage)
  - [Website](#website)
  - [Chrome Extension](#chrome-extension)
- [ML Model Architecture](#ml-model-architecture)
  - [HTMLGCNCNN](#htmlgcncnn)
  - [URLBERT](#urlbert)
- [Contact](#contact)

---

## Project Overview

Phishing attacks are one of the most common cyber threats, where malicious websites deceive users into revealing confidential information. PhishNet aims to combat this growing issue by detecting phishing websites using Machine Learning models and making these tools accessible to users through:
- A **website** for analyzing URLs.
- A **Chrome extension** for real-time phishing detection while browsing.

Key components of PhishNet include:
- Advanced Machine Learning models (**HTMLGCNCNN** and **URLBERT**) tailored for phishing detection.
- Comprehensive tools for manual and automatic phishing detection.

---

## Features

### **Website**
- Analyze URLs for phishing or legitimacy.
- Select from different detection models (**BERT** or **Graph CNN**).
- View and manage your **search history**.

### **Chrome Extension**
- **Manual URL Submission**: Analyze links directly from your browser.
- **Automatic Link Detection**: Scans webpages for phishing links in real time.
- Notifications for detected phishing links.

---

## Installation

### Website Access
1. Open your browser and navigate to the [PhishNet Website](#).
2. Register or log in to your account to start analyzing URLs.

### Chrome Extension
1. Install **Node Version Manager (NVM)**.
2. Run `nvm use` to switch to Node.js version **v20.15.1**.
3. Install dependencies with `npm install`.
4. Build the extension using `npm run webpack`.
5. Open Chrome and navigate to `chrome://extensions/`.
6. Enable **Developer Mode** and click **Load unpacked**.
7. Select the `dist` folder to complete the installation.

---

## Usage

### Website
1. Log in to the PhishNet website.
2. Enter a URL in the input field.
3. Choose the desired detection model: **BERT** or **Graph CNN**.
4. Click **Submit** to view the results.
5. Access your search history to review previous scans.

### Chrome Extension
1. Click the PhishNet icon in the Chrome toolbar.
2. Enter a URL for manual submission or enable **Automatic Link Detection** in the settings.
3. View detected phishing links in real time and receive notifications.

---

## ML Model Architecture

### **HTMLGCNCNN**
The HTMLGCNCNN model integrates Convolutional Neural Networks (CNN) and GraphSAGE to handle:
- **Sequential Data**: Analyzed using CNN layers for lexical patterns.
- **Graph Data**: Processed using GraphSAGE to capture DOM structures.

**Workflow**:
1. Sequential and graph data are processed by respective components.
2. Features are fused into a unified vector.
3. Classification layers output phishing/legitimate verdicts.

### **URLBERT**
URLBERT leverages a pre-trained BERT model for lexical and semantic URL analysis. It captures contextual relationships within URLs and outputs classification probabilities.

**Workflow**:
1. Tokenizes raw URLs into meaningful segments.
2. Processes segments using the BERT encoder.
3. Outputs phishing/legitimate classifications through a softmax layer.

---

## Contact

For support or inquiries, contact the PhishNet development team:
- **Arunav Sinha**: asinh060@uottawa.ca
- **James Couture**: jcout071@uottawa.ca
- **Alfred Genadri**: agena036@uottawa.ca
- **Adam Jasniewicz**: ajasn076@uottawa.ca
- **Juan Pablo Sanchez Garcia**: jsanc016@uottawa.ca

--- 

PhishNet: **Stay safe online with real-time phishing detection.**