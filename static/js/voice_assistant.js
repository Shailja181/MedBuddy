/**
 * Speech Synthesis & Voice Assistant Utilities for MedBuddy
 */

function speakVoice(text) {
    if (!('speechSynthesis' in window)) {
        console.warn("Speech synthesis not supported in this browser.");
        return;
    }
    window.speechSynthesis.cancel(); // Stop active speech
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.95;
    utterance.pitch = 1.0;
    
    // Select friendly voice if available
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find(v => v.lang.includes('en') && v.name.includes('Google') || v.name.includes('Natural'));
    if (preferredVoice) utterance.voice = preferredVoice;

    window.speechSynthesis.speak(utterance);
}

function readDietChartAloud(diet) {
    const text = `Here is your customized diet plan. ` +
                 `For Breakfast: ${diet.breakfast}. ` +
                 `For Lunch: ${diet.lunch}. ` +
                 `For Dinner: ${diet.dinner}. ` +
                 `Foods to avoid: ${diet.foods_to_avoid}.`;
    speakVoice(text);
}

function readFridgeMagnetAloud(magnet) {
    const text = `Your daily schedule. Morning: ${magnet.morning}. ` +
                 `Afternoon: ${magnet.afternoon}. Evening: ${magnet.evening}. Night: ${magnet.night}.`;
    speakVoice(text);
}