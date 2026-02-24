<?php

function categorizeBook($pages) {
if ($pages < 100) {
return "Light Read";
} elseif ($pages < 300) {
return "Standard Novel";
} else {
return "Epic Saga";
}
}

function recommendBook($genre){
	if($genre==="Fantasy"){
		return "A Game Of Thrones";
	}elseif($genre==="Sci-Fi"){
		return "Frankenstein"; // Corrected typo
	}elseif($genre==="Mystery"){
		return "Gone Girl"; // Changed recommendation to better fit the genre
	}else{
		return "Man's Search for Meaning"; // <-- **FIX 1: Added missing semicolon**
	}
}

$harryPotterPages = 600;
$genre = "Mystery"; // <-- **FIX 2: Removed leading '<'**
$category = categorizeBook($harryPotterPages);
$book = recommendBook($genre);
echo "Harry Potter is considered " . $category . ". The recommended book for your genre (" . $genre . ") is " . $book . ".";

?>