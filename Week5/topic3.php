<?php
$quote = "Happiness can be found even in the darkest of times, if one only
remembers to turn on the light.";

echo "Total number of character is ".strlen($quote);
echo "Total words is quote is :".str_word_count($quote);
if(stripos($quote, "Light")){
	echo "Light appears at:".strpos($quote, "Light");
}else{
	echo "<br> Light words not found in given quote.";
}
echo "<br> Replaced String is :".str_replace("darkest", "terriable", $quote);
// Question 1: Use strlen() to display the total number of characters
// Question 2: Use str_word_count() to count how many words are in the quote
// Question 3: Use strrev() to reverse the entire quotation
// Question 4: Use strpos() to check if the word "light" appears in the quote
// If it appears, display its position. If not, display a message.
// Question 5: Use str_replace() to replace the word "darkest" with "terrible"
// Then display the updated quote
?>