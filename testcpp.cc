#include "dom_tree_builder.h"
#include "dom.h"
#include "html_token.h"


void DomTreeBuilder::SetAttribute(Element &element, const std::vector<std::pair<std::string, std::string>> &attributes) {
	if (attributes.empty()) {
		return;
	}

	std::unordered_map<std::string, std::string> attributeMap;
	for (const auto& attribute : attributes) {
		attributeMap[attribute.first] = attribute.second;
	}
	element.setAttributeMap(std::move(attributeMap));
}

void DomTreeBuilder::HandleNoneState(std::unique_ptr<HTMLToken> token) {
	if (token->type() != HTMLToken::TokenType::kStartTag) {
		return;
	}

	domTree_ = std::make_unique<Element>(token->TagName());
	SetAttribute(*domTree_, token->Attributes());

	header_ = domTree_.get();
	state_ = State::kTagOpen;
}

void DomTreeBuilder::HandleTagOpenState(std::unique_ptr<HTMLToken> token) {
	std::unique_ptr<DomNode> currentNode = nullptr;
	
	switch (token->type()) {
	case HTMLToken::TokenType::kStartTag: {
		currentNode = std::make_unique<Element>(token->TagName());
		SetAttribute(*static_cast<Element *>(currentNode.get()), token->Attributes());
		currentNode->setParent(header_);
	}
	break;
	case HTMLToken::TokenType::kCharacter: {
		auto currentNode = std::make_unique<TextNode>(token->TagName());
		currentNode->setParent(header_);
	}
	break;
	case HTMLToken::TokenType::kEndTag: {
		header_ = header_->parent();
		state_ = State::kTagClose;
	}
	break;
	}

	if (currentNode) {
		DomNode* newHeader = currentNode.get();
		header_->addChild(std::move(currentNode));
		header_ = newHeader;
	}
}

void DomTreeBuilder::HandleTagCloseState(std::unique_ptr<HTMLToken> token) {
	std::unique_ptr<DomNode> currentNode = nullptr;

	switch (token->type()) {
	case HTMLToken::TokenType::kStartTag: {
		currentNode = std::make_unique<Element>(token->TagName());
		SetAttribute(*static_cast<Element*>(currentNode.get()), token->Attributes());
		currentNode->setParent(header_);
		DomNode* newHeader = currentNode.get();
		header_->addChild(std::move(currentNode));
		header_ = newHeader;
		state_ = State::kTagOpen;
	}
	break;

	case HTMLToken::TokenType::kCharacter: {
		currentNode = std::make_unique<TextNode>(token->TagName());
		currentNode->setParent(header_);
		header_->addChild(std::move(currentNode));
		state_ = State::kTagOpen;
	}
	break;
	}
}

void DomTreeBuilder::ConstructTreeFromHTMLToken(std::unique_ptr<HTMLToken> token) {
	switch (state_) {
	case State::kNone:
		HandleNoneState(std::move(token));
		break;
	case State::kTagOpen:
		HandleTagOpenState(std::move(token));
		break;
	case State::kTagClose:
		HandleTagCloseState(std::move(token));
		break;
	}
}

const Element &DomTreeBuilder::domTree() const
{ 
	return *domTree_;
}